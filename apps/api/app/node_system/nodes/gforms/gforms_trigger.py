"""Google Forms trigger node — polling-driven new-response detection.

One event: `new_response`. Cursor stores the last `submitted_at`
timestamp; first poll snapshots it, later polls emit every response
submitted strictly after the cursor (sorted by `lastSubmittedTime`
desc, so the newest arrives at index 0).

Output payload is already mapped — `answers` is `{question_title:
value}` instead of `{question_id: {textAnswers: ...}}` — so downstream
nodes don't have to know Form API's wire shape.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.repository import IntegrationTriggerStateRepository
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.gforms.gforms_node import (
    _build_question_id_to_title,
    _normalise_response,
)

logger = get_logger(__name__)

FORMS_API = "https://forms.googleapis.com/v1/forms"
PROVIDER = "google_forms"
DEFAULT_POLL_INTERVAL_SECONDS = 60


class GoogleFormsTriggerProperties(BaseModel):
    credential: str | None = None
    form_id: str = ""
    max_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    @field_validator("form_id", mode="before")
    @classmethod
    def _coerce_form_id(cls, value: Any) -> str:
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) else ""
        return str(value) if value is not None else ""


class GoogleFormsTriggerNode(BaseNode[GoogleFormsTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleFormsTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gforms_response",
            name="Google Forms",
            category="trigger",
            description=(
                "Fires once per response submitted to the picked form. First "
                "poll snapshots silently; later polls emit one execution per "
                "new submission with answers keyed by question title."
            ),
            icon="si:SiGoogleforms",
            color="#673ab7",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "form_id",
                    "label": "Form",
                    "type": "google-file",
                    "required": True,
                    "typeOptions": {
                        "mimeType": "application/vnd.google-apps.form",
                        "placeholder": "Pick a form…",
                        "searchPlaceholder": "Search your forms…",
                        "createPlaceholder": "Create new form…",
                    },
                },
                {
                    "name": "max_per_poll",
                    "label": "Max responses per poll",
                    "type": "number",
                    "default": 25,
                    "mode": "advanced",
                },
                {
                    "name": "poll_interval_seconds",
                    "label": "Poll interval (seconds)",
                    "type": "number",
                    "default": DEFAULT_POLL_INTERVAL_SECONDS,
                    "mode": "advanced",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "response_id", "type": "string"},
                {"label": "form_id", "type": "string"},
                {"label": "submitted_at", "type": "string"},
                {"label": "respondent_email", "type": "string"},
                {"label": "answers", "type": "object"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Scheduler-dispatched payload — pass through.
        if (
            isinstance(input_data, dict)
            and input_data.get("response_id")
            and input_data.get("answers") is not None
        ):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")
        if not self.props.form_id:
            return NodeResult(success=False, error="Form is required.")

        workflow_id = getattr(context, "workflow_id", None)
        node_id = getattr(context, "node_id", None)
        workspace_id = getattr(context, "workspace_id", None)
        db = getattr(context, "db", None)
        wf_uuid = _safe_uuid(workflow_id)
        ws_uuid = _safe_uuid(workspace_id)
        if wf_uuid is None or ws_uuid is None or db is None or not node_id:
            return await self._stateless_preview(token)

        repo = IntegrationTriggerStateRepository(db)
        state = await repo.get(wf_uuid, node_id)
        cursor = state.cursor if state else None

        try:
            matches, new_cursor = await self.poll(token, cursor)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Google Forms API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("GoogleFormsTriggerNode poll failed: %s", exc, exc_info=True)
            return NodeResult(success=False, error=str(exc))

        await repo.upsert(
            workflow_id=wf_uuid,
            workspace_id=ws_uuid,
            node_id=node_id,
            provider=PROVIDER,
            cursor=new_cursor,
            next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
            last_error=None,
        )
        await db.commit()

        if not matches:
            return NodeResult(
                success=True,
                output_data={
                    "matched": 0,
                    "responses": [],
                    "last_submitted_at": new_cursor.get("last_submitted_at"),
                },
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=matches[0])

    # ── public poll API ───────────────────────────────────────────────

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        form_id = self.props.form_id
        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))

        async with httpx.AsyncClient(timeout=30) as client:
            titles = await _fetch_titles(client, headers, form_id)
            params: dict[str, str] = {"pageSize": str(max_per_poll * 2)}
            last = (cursor or {}).get("last_submitted_at")
            if last:
                params["filter"] = f"timestamp > {last}"
            r = await client.get(f"{FORMS_API}/{form_id}/responses", headers=headers, params=params)
            r.raise_for_status()
            raw = r.json().get("responses") or []

        # First poll — snapshot the newest timestamp without emitting.
        if not last:
            newest = _newest_timestamp(raw)
            return [], {"last_submitted_at": newest or _utc_now_rfc3339()}

        # API returns responses descending by last-submitted; emit oldest
        # first so the workflow's natural order is the form's order.
        sorted_resp = sorted(
            raw,
            key=lambda r: r.get("lastSubmittedTime") or r.get("createTime") or "",
        )
        emitted = sorted_resp[:max_per_poll]
        matches = [_normalise_response(resp, titles) for resp in emitted]

        # Advance cursor only as far as the newest *emitted* response.
        # Anything we deferred keeps the prior cursor on its right so the
        # next tick re-considers it.
        new_last = (
            (emitted[-1].get("lastSubmittedTime") or emitted[-1].get("createTime") or last)
            if emitted
            else last
        )
        return matches, {"last_submitted_at": new_last}

    async def _stateless_preview(self, token: str) -> NodeResult:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            titles = await _fetch_titles(client, headers, self.props.form_id)
            r = await client.get(
                f"{FORMS_API}/{self.props.form_id}/responses",
                headers=headers,
                params={"pageSize": "1"},
            )
            r.raise_for_status()
            raw = r.json().get("responses") or []
        if not raw:
            return NodeResult(
                success=True,
                output_data={"matched": 0, "responses": []},
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=_normalise_response(raw[0], titles))


# ── helpers ─────────────────────────────────────────────────────────────


async def _fetch_titles(
    client: httpx.AsyncClient, headers: dict[str, str], form_id: str
) -> dict[str, str]:
    r = await client.get(f"{FORMS_API}/{form_id}", headers=headers)
    r.raise_for_status()
    return _build_question_id_to_title(r.json())


def _newest_timestamp(responses: list[dict[str, Any]]) -> str | None:
    best: str | None = None
    for r in responses:
        t = r.get("lastSubmittedTime") or r.get("createTime")
        if t and (best is None or t > best):
            best = t
    return best


def _utc_now_rfc3339() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _next_poll_at(interval_seconds: int) -> datetime:
    seconds = max(30, min(int(interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS), 60 * 60))
    return datetime.now(UTC) + timedelta(seconds=seconds)


# ── scheduler integration ──────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    node = GoogleFormsTriggerNode.__new__(GoogleFormsTriggerNode)
    node.props = GoogleFormsTriggerProperties(
        credential=None,
        form_id=props.get("form_id") or "",
        max_per_poll=int(props.get("max_per_poll") or 25),
        poll_interval_seconds=int(
            props.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS
        ),
    )
    return await node.poll(token, cursor)


def _register() -> None:
    try:
        from apps.api.app.execution_engine.scheduler.integration_polling import (
            register_poller,
        )
    except Exception:  # noqa: BLE001
        return
    register_poller(
        node_type="trigger.gforms_response",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()

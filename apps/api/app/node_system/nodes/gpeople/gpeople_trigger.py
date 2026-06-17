"""Google Contacts trigger node — polling-driven add + update detection.

Two event types, separate cursor shapes:

  - `contact_added` — fires once per contact newly added to the user's
    My Contacts. Cursor stores the resource-name set we've already
    surfaced; first poll snapshots it silently, later polls emit on new
    resource names.

  - `contact_updated` — fires once per contact whose `etag` changed.
    Cursor stores `{resource_name: etag}`. First poll snapshots etags
    silently, later polls emit on every etag mismatch.

Swapping `event_type` between polls is treated as a first poll for the
new event — keeps the cursor shapes from cross-polluting.
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
from apps.api.app.node_system.nodes.gpeople.gpeople_node import _flatten_contact

logger = get_logger(__name__)

PEOPLE_API = "https://people.googleapis.com/v1"
PROVIDER = "google_people"
DEFAULT_POLL_INTERVAL_SECONDS = 60

EVENT_ADDED = "contact_added"
EVENT_UPDATED = "contact_updated"
EVENT_TYPES = (EVENT_ADDED, EVENT_UPDATED)

# Fields we pull per poll. Keep slim for the trigger so the response
# stays small; downstream `get_contact` can hydrate when needed.
_POLL_PERSON_FIELDS = "names,emailAddresses,phoneNumbers,organizations,metadata"


class GooglePeopleTriggerProperties(BaseModel):
    credential: str | None = None
    event_type: str = EVENT_ADDED
    max_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    @field_validator("event_type", mode="before")
    @classmethod
    def _coerce_event_type(cls, value: Any) -> str:
        v = str(value or "").strip().lower()
        return v if v in EVENT_TYPES else EVENT_ADDED


class GooglePeopleTriggerNode(BaseNode[GooglePeopleTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GooglePeopleTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gpeople_change",
            name="Google Contacts",
            category="trigger",
            description=(
                "Fires when contacts are added to or updated in your Google "
                "Contacts. First poll snapshots silently; later polls emit "
                "one execution per matching contact."
            ),
            icon="si:SiGooglecontacts",
            color="#1a73e8",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": EVENT_ADDED,
                    "options": [
                        {"label": "Contact added", "value": EVENT_ADDED},
                        {"label": "Contact updated", "value": EVENT_UPDATED},
                    ],
                },
                {
                    "name": "max_per_poll",
                    "label": "Max events per poll",
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
                {"label": "resource_name", "type": "string"},
                {"label": "display_name", "type": "string"},
                {"label": "emails", "type": "array"},
                {"label": "phones", "type": "array"},
                {"label": "event_type", "type": "string"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if (
            isinstance(input_data, dict)
            and input_data.get("resource_name")
            and input_data.get("event_type") in EVENT_TYPES
        ):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

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
                error=f"People API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("GooglePeopleTriggerNode poll failed: %s", exc, exc_info=True)
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
                    "contacts": [],
                    **_cursor_summary(new_cursor),
                },
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=matches[0])

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        event_type = self.props.event_type
        prior_event = (cursor or {}).get("event_type")
        if cursor and prior_event != event_type:
            cursor = None

        connections = await _fetch_all_connections(headers)

        if event_type == EVENT_UPDATED:
            return self._diff_updated(connections, cursor)
        return self._diff_added(connections, cursor)

    # ── per-event diff ────────────────────────────────────────────────

    def _diff_added(
        self,
        connections: list[dict[str, Any]],
        cursor: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        current_ids = [str(p.get("resourceName")) for p in connections if p.get("resourceName")]
        prior_ids = (cursor or {}).get("known_ids")
        if not isinstance(prior_ids, list):
            return [], {"event_type": EVENT_ADDED, "known_ids": current_ids}

        known = set(prior_ids)
        matches: list[dict[str, Any]] = []
        emitted_ids: set[str] = set()
        for p in connections:
            rn = str(p.get("resourceName") or "")
            if not rn or rn in known:
                continue
            matches.append({**_flatten_contact(p), "event_type": EVENT_ADDED})
            emitted_ids.add(rn)
            if len(matches) >= max_per_poll:
                break
        next_known = list(known | emitted_ids)
        return matches, {"event_type": EVENT_ADDED, "known_ids": next_known}

    def _diff_updated(
        self,
        connections: list[dict[str, Any]],
        cursor: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        max_per_poll = max(1, min(int(self.props.max_per_poll or 25), 500))
        now_etags: dict[str, str] = {
            str(p.get("resourceName")): str(p.get("etag") or "")
            for p in connections
            if p.get("resourceName")
        }
        prior = (cursor or {}).get("etags")
        if not isinstance(prior, dict):
            return [], {"event_type": EVENT_UPDATED, "etags": now_etags}

        matches: list[dict[str, Any]] = []
        emitted_ids: set[str] = set()
        for p in connections:
            rn = str(p.get("resourceName") or "")
            now_tag = now_etags.get(rn, "")
            prior_tag = prior.get(rn)
            if prior_tag is None or not now_tag:
                # New contact — belongs to `contact_added`, not here.
                # Silently record so a later update fires though.
                continue
            if now_tag != prior_tag:
                matches.append({**_flatten_contact(p), "event_type": EVENT_UPDATED})
                emitted_ids.add(rn)
                if len(matches) >= max_per_poll:
                    break

        # Advance only emitted; defer the rest by keeping their prior etag.
        next_etags = dict(prior)
        for rn, tag in now_etags.items():
            if rn in emitted_ids or rn not in prior:
                next_etags[rn] = tag
        return matches, {"event_type": EVENT_UPDATED, "etags": next_etags}

    async def _stateless_preview(self, token: str) -> NodeResult:
        headers = {"Authorization": f"Bearer {token}"}
        connections = await _fetch_all_connections(headers, max_total=1)
        if not connections:
            return NodeResult(
                success=True,
                output_data={"matched": 0, "contacts": []},
                handled_successors=True,
            )
        return NodeResult(
            success=True,
            output_data={
                **_flatten_contact(connections[0]),
                "event_type": self.props.event_type,
            },
        )


# ── helpers ─────────────────────────────────────────────────────────────


async def _fetch_all_connections(
    headers: dict[str, str], max_total: int = 1000
) -> list[dict[str, Any]]:
    """Walk every page of `people/me/connections` up to `max_total`."""
    out: list[dict[str, Any]] = []
    page_token: str | None = None
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            params: dict[str, Any] = {
                "personFields": _POLL_PERSON_FIELDS,
                "pageSize": 1000,
                "sortOrder": "LAST_MODIFIED_DESCENDING",
            }
            if page_token:
                params["pageToken"] = page_token
            r = await client.get(
                f"{PEOPLE_API}/people/me/connections",
                headers=headers,
                params=params,
            )
            r.raise_for_status()
            data = r.json()
            out.extend(data.get("connections") or [])
            page_token = data.get("nextPageToken")
            if not page_token or len(out) >= max_total:
                break
    return out[:max_total]


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


def _cursor_summary(cursor: dict[str, Any]) -> dict[str, Any]:
    event = cursor.get("event_type") or EVENT_ADDED
    if event == EVENT_UPDATED:
        return {"event_type": event, "tracked_contacts": len(cursor.get("etags") or {})}
    return {"event_type": event, "known_contacts": len(cursor.get("known_ids") or [])}


# ── scheduler integration ──────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    node = GooglePeopleTriggerNode.__new__(GooglePeopleTriggerNode)
    node.props = GooglePeopleTriggerProperties(
        credential=None,
        event_type=str(props.get("event_type") or EVENT_ADDED),
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
        node_type="trigger.gpeople_change",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()

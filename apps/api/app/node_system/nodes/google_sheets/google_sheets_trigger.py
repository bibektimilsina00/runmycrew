"""Google Sheets trigger node — polling new-row + row-update detection.

Two event types, distinct cursor shapes:

  - `row_added` — fires once per row appended to the sheet.
      cursor: ``{event_type: "row_added", last_row_count: N}``
      Initial poll snapshots the populated row count and emits nothing;
      later polls emit one match per row in the range (N, current_count].

  - `row_updated` — fires once per row whose value changed in place.
      cursor: ``{event_type: "row_updated", row_hashes: [sha1, sha1, ...]}``
      Initial poll snapshots a SHA-1 hash per row and emits nothing;
      later polls re-hash and emit one match per index whose hash moved.
      Newly *added* rows are intentionally NOT emitted here — that's the
      `row_added` event's job; this trigger is about in-place edits.

A cursor whose ``event_type`` doesn't match the node's current setting
is treated as a first poll — switching event types resnapshots cleanly
rather than misreading the prior shape.

Range model
  - User picks a sheet (tab); defaults to ``Sheet1``.
  - Reads columns A:Z by default (advanced field bumps the last column).
    Sheets returns only populated rows, so ``len(response.values)``
    is the populated count.
"""

from __future__ import annotations

import hashlib
import json
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

logger = get_logger(__name__)

SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"
PROVIDER = "google_sheets"
DEFAULT_POLL_INTERVAL_SECONDS = 60
DEFAULT_LAST_COLUMN = "Z"

EVENT_ROW_ADDED = "row_added"
EVENT_ROW_UPDATED = "row_updated"
EVENT_TYPES = (EVENT_ROW_ADDED, EVENT_ROW_UPDATED)


class GoogleSheetsTriggerProperties(BaseModel):
    credential: str | None = None
    event_type: str = EVENT_ROW_ADDED
    spreadsheet_id: str = ""
    sheet_name: str = "Sheet1"
    # Last column to read. Wider sheets bump this; narrow sheets shrink
    # it to keep payloads small.
    last_column: str = DEFAULT_LAST_COLUMN
    max_rows_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    @field_validator("spreadsheet_id", mode="before")
    @classmethod
    def _coerce_spreadsheet_id(cls, value: Any) -> str:
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) else ""
        return str(value) if value is not None else ""

    @field_validator("sheet_name", mode="before")
    @classmethod
    def _coerce_sheet_name(cls, value: Any) -> str:
        if isinstance(value, dict):
            v = value.get("title")
            return str(v) if isinstance(v, str) and v else "Sheet1"
        if value in (None, ""):
            return "Sheet1"
        return str(value)

    @field_validator("event_type", mode="before")
    @classmethod
    def _coerce_event_type(cls, value: Any) -> str:
        v = str(value or "").strip().lower()
        return v if v in EVENT_TYPES else EVENT_ROW_ADDED


class GoogleSheetsTriggerNode(BaseNode[GoogleSheetsTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleSheetsTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.google_sheets",
            name="Google Sheets",
            category="trigger",
            description=(
                "Fires when rows are added or updated in the picked sheet. "
                "Pick the event below — `Row added` watches the bottom of the "
                "sheet, `Row updated` hashes each row so in-place edits emit."
            ),
            icon="google-sheets",
            color="#1c1c1c",
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
                    "default": EVENT_ROW_ADDED,
                    "options": [
                        {"label": "Row added", "value": EVENT_ROW_ADDED},
                        {"label": "Row updated", "value": EVENT_ROW_UPDATED},
                    ],
                },
                {
                    "name": "spreadsheet_id",
                    "label": "Spreadsheet",
                    "type": "google-file",
                    "required": True,
                    "typeOptions": {
                        "mimeType": "application/vnd.google-apps.spreadsheet",
                        "placeholder": "Pick a spreadsheet…",
                        "searchPlaceholder": "Search your spreadsheets…",
                        "createPlaceholder": "Create new spreadsheet…",
                    },
                },
                {
                    "name": "sheet_name",
                    "label": "Sheet (tab)",
                    "type": "gsheet-tab",
                    "typeOptions": {"valueAs": "title"},
                    "default": "Sheet1",
                    "required": True,
                },
                {
                    "name": "last_column",
                    "label": "Last column",
                    "type": "string",
                    "default": DEFAULT_LAST_COLUMN,
                    "placeholder": "Z",
                    "description": "Column letter to read up to. Z covers 26 columns.",
                    "mode": "advanced",
                },
                {
                    "name": "max_rows_per_poll",
                    "label": "Max rows per poll",
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
                {"label": "row_index", "type": "number"},
                {"label": "values", "type": "array"},
                {"label": "spreadsheet_id", "type": "string"},
                {"label": "sheet_name", "type": "string"},
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
        # Scheduler-dispatched payload — pass through.
        if (
            isinstance(input_data, dict)
            and input_data.get("row_index")
            and input_data.get("values") is not None
        ):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")
        if not self.props.spreadsheet_id:
            return NodeResult(success=False, error="Spreadsheet is required.")

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
            rows, new_cursor = await self.poll(token, cursor)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Google Sheets API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("GoogleSheetsTriggerNode poll failed: %s", exc, exc_info=True)
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

        if not rows:
            return NodeResult(
                success=True,
                output_data={"matched": 0, "rows": [], **_cursor_summary(new_cursor)},
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=rows[0])

    # ── public poll API ───────────────────────────────────────────────

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        sid = self.props.spreadsheet_id
        sheet_name = self._sheet_name()
        last_col = self._last_column()
        max_rows = max(1, min(int(self.props.max_rows_per_poll or 25), 500))
        event_type = self.props.event_type

        async with httpx.AsyncClient(timeout=30) as client:
            rng = f"{sheet_name}!A:{last_col}"
            resp = await client.get(
                f"{SHEETS_API}/{sid}/values/{rng}",
                headers=headers,
                params={"majorDimension": "ROWS"},
            )
            resp.raise_for_status()
            values = resp.json().get("values") or []

        # Cursor from a different event_type → first poll for the new event.
        prior_event = (cursor or {}).get("event_type")
        if cursor and prior_event != event_type:
            cursor = None

        if event_type == EVENT_ROW_UPDATED:
            return self._diff_row_updated(values, cursor, sid, sheet_name, max_rows)
        return self._diff_row_added(values, cursor, sid, sheet_name, max_rows)

    # ── per-event diff functions ──────────────────────────────────────

    def _diff_row_added(
        self,
        values: list[list[Any]],
        cursor: dict[str, Any] | None,
        sid: str,
        sheet_name: str,
        max_rows: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        current_count = len(values)
        last_count_raw = (cursor or {}).get("last_row_count", -1)
        try:
            last_count = int(last_count_raw)
        except (TypeError, ValueError):
            last_count = -1

        # First poll → snapshot only.
        if last_count < 0:
            return [], {"event_type": EVENT_ROW_ADDED, "last_row_count": current_count}

        # Sheet shrunk → silent rewind.
        if current_count <= last_count:
            return [], {"event_type": EVENT_ROW_ADDED, "last_row_count": current_count}

        new_rows = values[last_count:current_count]
        if len(new_rows) > max_rows:
            new_rows = new_rows[:max_rows]
            current_count = last_count + max_rows

        payloads = [
            self._payload(sid, sheet_name, last_count + 1 + i, row, EVENT_ROW_ADDED)
            for i, row in enumerate(new_rows)
        ]
        return payloads, {"event_type": EVENT_ROW_ADDED, "last_row_count": current_count}

    def _diff_row_updated(
        self,
        values: list[list[Any]],
        cursor: dict[str, Any] | None,
        sid: str,
        sheet_name: str,
        max_rows: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        now_hashes = [_hash_row(r) for r in values]
        prior = (cursor or {}).get("row_hashes")

        # First poll → snapshot hashes, no emit.
        if not isinstance(prior, list):
            return [], {"event_type": EVENT_ROW_UPDATED, "row_hashes": now_hashes}

        matches: list[dict[str, Any]] = []
        for idx in range(min(len(now_hashes), len(prior))):
            if now_hashes[idx] != prior[idx]:
                matches.append(
                    self._payload(sid, sheet_name, idx + 1, values[idx], EVENT_ROW_UPDATED)
                )
                if len(matches) >= max_rows:
                    break
        # Persist the *full* new hashes array — even when fanout was
        # capped — so the deferred rows stay flagged for the next tick.
        if len(matches) >= max_rows:
            # Roll back the hashes for not-yet-emitted indices so they
            # remain "changed" relative to the cursor.
            cutoff_idx = matches[-1]["row_index"]  # 1-based
            persisted_hashes = list(now_hashes)
            for j in range(cutoff_idx, min(len(now_hashes), len(prior))):
                # Only roll back rows that still differ; ones that match
                # are stable and should advance.
                if now_hashes[j] != prior[j]:
                    persisted_hashes[j] = prior[j]
            return matches, {"event_type": EVENT_ROW_UPDATED, "row_hashes": persisted_hashes}
        return matches, {"event_type": EVENT_ROW_UPDATED, "row_hashes": now_hashes}

    # ── helpers ───────────────────────────────────────────────────────

    def _sheet_name(self) -> str:
        return (self.props.sheet_name or "Sheet1").strip() or "Sheet1"

    def _last_column(self) -> str:
        return (
            self.props.last_column or DEFAULT_LAST_COLUMN
        ).strip().upper() or DEFAULT_LAST_COLUMN

    def _payload(
        self,
        sid: str,
        sheet_name: str,
        row_index: int,
        row: list[Any],
        event_type: str,
    ) -> dict[str, Any]:
        return {
            "row_index": row_index,
            "values": row,
            "spreadsheet_id": sid,
            "sheet_name": sheet_name,
            "event_type": event_type,
        }

    async def _stateless_preview(self, token: str) -> NodeResult:
        """Preview / listen path with no DB context — return the most
        recent row in the sheet as a one-shot preview match."""
        headers = {"Authorization": f"Bearer {token}"}
        sheet_name = self._sheet_name()
        last_col = self._last_column()
        async with httpx.AsyncClient(timeout=30) as client:
            rng = f"{sheet_name}!A:{last_col}"
            resp = await client.get(
                f"{SHEETS_API}/{self.props.spreadsheet_id}/values/{rng}",
                headers=headers,
                params={"majorDimension": "ROWS"},
            )
            resp.raise_for_status()
            values = resp.json().get("values") or []
        if not values:
            return NodeResult(
                success=True,
                output_data={"matched": 0, "rows": [], "last_row_count": 0},
                handled_successors=True,
            )
        last = values[-1]
        return NodeResult(
            success=True,
            output_data=self._payload(
                self.props.spreadsheet_id,
                sheet_name,
                len(values),
                last,
                self.props.event_type,
            ),
        )


# ── module helpers ──────────────────────────────────────────────────────


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


def _hash_row(row: list[Any]) -> str:
    """Stable per-row fingerprint. JSON-encode to keep numeric vs string
    differences (e.g. "0" vs 0) distinct — Sheets returns strings for
    formulas evaluating to numbers in some response shapes."""
    blob = json.dumps(row, default=str, ensure_ascii=False, sort_keys=False)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def _cursor_summary(cursor: dict[str, Any]) -> dict[str, Any]:
    """Slim down the persisted cursor for output — emitting the full
    `row_hashes` array on every empty poll would balloon execution
    logs."""
    event = cursor.get("event_type") or EVENT_ROW_ADDED
    if event == EVENT_ROW_UPDATED:
        hashes = cursor.get("row_hashes") or []
        return {"event_type": event, "tracked_rows": len(hashes)}
    return {"event_type": event, "last_row_count": cursor.get("last_row_count")}


# ── scheduler integration ────────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    node = GoogleSheetsTriggerNode.__new__(GoogleSheetsTriggerNode)
    node.props = GoogleSheetsTriggerProperties(
        credential=None,
        event_type=str(props.get("event_type") or EVENT_ROW_ADDED),
        spreadsheet_id=props.get("spreadsheet_id") or "",
        sheet_name=props.get("sheet_name") or "Sheet1",
        last_column=str(props.get("last_column") or DEFAULT_LAST_COLUMN),
        max_rows_per_poll=int(props.get("max_rows_per_poll") or 25),
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
        node_type="trigger.google_sheets",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()

"""Google Analytics 4 action node — one node, 13 operations.

Data API v1beta (reporting):
  - ``run_report``          — dimensions + metrics over a date range
  - ``run_realtime_report`` — last 30 minutes
  - ``run_pivot_report``    — pivoted slice of a report
  - ``batch_run_reports``   — run multiple reports in one call
  - ``check_compatibility`` — verify a dimension / metric combo
  - ``get_metadata``        — list available dimensions + metrics on a property

Admin API v1beta (configuration reads):
  - ``list_accounts``           — GA4 accounts the user can see
  - ``list_properties``         — properties under an account
  - ``get_property``            — details for one property
  - ``list_data_streams``       — web / iOS / Android streams under a property
  - ``list_key_events``         — conversion (key) events
  - ``list_custom_dimensions``  — user-defined dimensions
  - ``list_custom_metrics``     — user-defined metrics

OAuth scope: ``analytics.readonly`` (added to GoogleOAuthProvider).
Covers both APIs read-only — no write operations exposed today.

Notes from build
  - GA4 property names follow ``properties/{id}``. The picker emits
    ``{id, name, displayName, account}``; the runtime coerces down to
    the canonical ``properties/{id}`` path. Bare numeric ids and full
    paths both pass through.
  - ``dimensions`` / ``metrics`` accept either a comma-separated string
    or a JSON array. We send the Data API the verbose ``[{name: x}]``
    shape it requires.
  - Filters / order-by / pivot config are forwarded verbatim as JSON
    so workflow authors keep the full Data API surface available
    without inventing intermediate shapes for every knob.
  - Date inputs (``start_date`` / ``end_date``) accept Data API
    relative strings (``today``, ``yesterday``, ``NdaysAgo``) and
    absolute ``YYYY-MM-DD``.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.errors import make_structured_error
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

DATA_API = "https://analyticsdata.googleapis.com/v1beta"
ADMIN_API = "https://analyticsadmin.googleapis.com/v1beta"


def format_ga4_error(status_code: int, body: str) -> str:
    """Turn a GA4 API error into a structured error payload.

    Common setup gaps:
      * **403 PERMISSION_DENIED** — the connected account isn't
        granted access to this GA4 property, OR the Analytics API
        isn't enabled for the GCP project hosting the OAuth client.
      * **404 NOT_FOUND** — property id wrong, or the account can't
        see it.
      * **400** — invalid dimension / metric name, or filter shape.

    Unhandled statuses fall through to plain string so the default
    renderer keeps working.
    """
    snippet = (body or "").strip()[:600]
    lower = snippet.lower()

    if status_code == 403 and "permission" in lower:
        return make_structured_error(
            "GA4 rejected the request",
            summary=(
                "The connected Google account doesn't have access to "
                "this GA4 property, or the Analytics APIs aren't "
                "enabled for the GCP project hosting the OAuth client."
            ),
            actions=[
                "Add the connected Google account as a Viewer (or higher) on the GA4 property in analytics.google.com → Admin → Property Access Management.",
                "GCP Console → APIs & Services → Library → enable `analyticsdata.googleapis.com` and `analyticsadmin.googleapis.com`.",
                "Disconnect + reconnect the Google credential to grant the `analytics.readonly` scope if you connected before today.",
            ],
            raw=snippet,
        )

    if status_code == 404:
        return make_structured_error(
            "GA4 resource not found",
            summary=(
                "The property id is wrong, the property was deleted, "
                "or the connected account can't see it."
            ),
            actions=[
                "Re-open the property picker and re-select.",
                "Verify the id matches `properties/{numeric}` exactly.",
            ],
            raw=snippet,
        )

    if status_code == 400:
        return make_structured_error(
            "GA4 request invalid",
            summary=(
                "The Data API rejected the request shape — most often a "
                "misspelled dimension / metric name, an invalid date "
                "range, or a filter that references an unknown field."
            ),
            actions=[
                "Use `get_metadata` to list every dimension and metric the property supports.",
                "Or use `check_compatibility` to verify the dimension + metric combination before running the report.",
            ],
            raw=snippet,
        )

    if status_code == 429:
        return make_structured_error(
            "GA4 quota exceeded",
            summary=(
                "The project ran out of GA4 API quota for this window. "
                "Calls resume once the quota refills."
            ),
            actions=[
                "Wait and retry — quota refills automatically.",
                "GCP Console → IAM & Admin → Quotas if you need a higher cap.",
            ],
            raw=snippet,
        )

    return f"GA4 API error {status_code}: {snippet or '(no body)'}"


_RELATIVE_DATE_RE = re.compile(r"^(?:today|yesterday|\d+daysAgo)$", re.IGNORECASE)
_ABSOLUTE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _normalise_date(raw: str) -> str:
    """Pass through Data API-shaped dates. Trim whitespace, normalise
    case for relative strings."""
    raw = raw.strip()
    if not raw:
        return raw
    if _ABSOLUTE_DATE_RE.match(raw):
        return raw
    if _RELATIVE_DATE_RE.match(raw):
        # API is case-sensitive on `NdaysAgo`; lowercase preserves it.
        return raw.lower() if not raw.endswith("Ago") else raw
    # Unknown shape — forward verbatim; the API gives a clear 400.
    return raw


def _parse_name_list(raw: Any) -> list[str]:
    """Accept a comma-separated string, JSON array, or list of strings
    and return a clean list of names."""
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        candidate = raw.strip()
        if candidate.startswith("["):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except json.JSONDecodeError:
                pass
        return [p.strip() for p in candidate.split(",") if p.strip()]
    raise ValueError(f"Expected a comma-separated string or list, got {type(raw).__name__}.")


def _to_property_name(raw: str) -> str:
    """Normalise a property identifier.

    Bare numeric id (``123456789``) → ``properties/123456789``.
    Full path passes through unchanged.
    """
    raw = raw.strip()
    if not raw:
        return raw
    return raw if raw.startswith("properties/") else f"properties/{raw}"


def _to_account_name(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return raw
    return raw if raw.startswith("accounts/") else f"accounts/{raw}"


def _coerce_json_field(raw: Any) -> Any:
    """Accept dict, list, or JSON string. Empty string → None."""
    if raw in (None, "", [], {}):
        return None
    if isinstance(raw, dict | list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Field must be valid JSON: {exc.msg}") from exc
    raise ValueError(f"Expected object / array / JSON string, got {type(raw).__name__}.")


class GoogleAnalyticsProperties(BaseModel):
    credential: str | None = None
    operation: str = "run_report"

    # Property + account identifiers
    property: str | None = None
    account: str | None = None

    # run_report / run_realtime_report / run_pivot_report shared inputs
    dimensions: Any = None
    metrics: Any = None
    start_date: str | None = None
    end_date: str | None = None
    limit: int | None = None
    offset: int | None = None
    dimension_filter: Any = None
    metric_filter: Any = None
    order_by: Any = None
    currency_code: str | None = None
    keep_empty_rows: bool = False

    # run_pivot_report
    pivots: Any = None

    # batch_run_reports
    requests_body: Any = None  # full {requests: [...]} payload

    # check_compatibility
    compatibility_filter: str | None = None  # COMPATIBLE / INCOMPATIBLE / COMPATIBILITY_UNSPECIFIED

    # list_* paging
    page_size: int | None = None
    page_token: str | None = None

    @field_validator("property", mode="before")
    @classmethod
    def _coerce_property(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        if isinstance(value, dict):
            v = value.get("id") or value.get("name") or ""
            if not v:
                return None
            return _to_property_name(str(v))
        return _to_property_name(str(value))

    @field_validator("account", mode="before")
    @classmethod
    def _coerce_account(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        if isinstance(value, dict):
            v = value.get("id") or value.get("name") or ""
            if not v:
                return None
            return _to_account_name(str(v))
        return _to_account_name(str(value))


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GoogleAnalyticsNode(BaseNode[GoogleAnalyticsProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleAnalyticsProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.ga4",
            name="Google Analytics 4",
            category="integration",
            description=(
                "Query Google Analytics 4 properties — run reports, "
                "fetch metadata, list accounts / properties / data "
                "streams / conversion events. Read-only against both "
                "the Data API and the Admin API."
            ),
            icon="google-analytics",
            color="#ffffff",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "run_report",
                    "options": [
                        {"label": "Run report", "value": "run_report"},
                        {
                            "label": "Run realtime report (last 30 min)",
                            "value": "run_realtime_report",
                        },
                        {"label": "Run pivot report", "value": "run_pivot_report"},
                        {"label": "Batch run reports", "value": "batch_run_reports"},
                        {"label": "Check compatibility", "value": "check_compatibility"},
                        {
                            "label": "Get metadata (available dimensions / metrics)",
                            "value": "get_metadata",
                        },
                        {"label": "List accounts", "value": "list_accounts"},
                        {"label": "List properties (under an account)", "value": "list_properties"},
                        {"label": "Get property", "value": "get_property"},
                        {"label": "List data streams", "value": "list_data_streams"},
                        {"label": "List key (conversion) events", "value": "list_key_events"},
                        {"label": "List custom dimensions", "value": "list_custom_dimensions"},
                        {"label": "List custom metrics", "value": "list_custom_metrics"},
                    ],
                },
                {
                    "name": "property",
                    "label": "Property",
                    "type": "ga4-property",
                    "required": True,
                    "condition": _cond_any(
                        "run_report",
                        "run_realtime_report",
                        "run_pivot_report",
                        "batch_run_reports",
                        "check_compatibility",
                        "get_metadata",
                        "get_property",
                        "list_data_streams",
                        "list_key_events",
                        "list_custom_dimensions",
                        "list_custom_metrics",
                    ),
                },
                {
                    "name": "account",
                    "label": "Account",
                    "type": "string",
                    "required": True,
                    "placeholder": "accounts/123456789  or  123456789",
                    "description": (
                        "Numeric account id, or the full `accounts/...` "
                        "resource name. Run List accounts first to find it."
                    ),
                    "condition": _cond("list_properties"),
                },
                # Report inputs
                {
                    "name": "dimensions",
                    "label": "Dimensions",
                    "type": "string",
                    "placeholder": "country,deviceCategory",
                    "description": (
                        "Comma-separated dimension names (or a JSON array). "
                        "Pull the full list with `get_metadata`."
                    ),
                    "condition": _cond_any("run_report", "run_realtime_report", "run_pivot_report"),
                },
                {
                    "name": "metrics",
                    "label": "Metrics",
                    "type": "string",
                    "required": True,
                    "placeholder": "activeUsers,sessions,screenPageViews",
                    "description": (
                        "Comma-separated metric names (or a JSON array). "
                        "Pull the full list with `get_metadata`."
                    ),
                    "condition": _cond_any(
                        "run_report",
                        "run_realtime_report",
                        "run_pivot_report",
                        "check_compatibility",
                    ),
                },
                {
                    "name": "start_date",
                    "label": "Start date",
                    "type": "string",
                    "required": True,
                    "default": "30daysAgo",
                    "placeholder": "30daysAgo  or  2024-01-01",
                    "description": (
                        "GA4 accepts relative (`today`, `yesterday`, "
                        "`NdaysAgo`) or absolute `YYYY-MM-DD` dates."
                    ),
                    "condition": _cond_any("run_report", "run_pivot_report"),
                },
                {
                    "name": "end_date",
                    "label": "End date",
                    "type": "string",
                    "required": True,
                    "default": "today",
                    "placeholder": "today  or  2024-12-31",
                    "condition": _cond_any("run_report", "run_pivot_report"),
                },
                {
                    "name": "limit",
                    "label": "Row limit",
                    "type": "number",
                    "default": 1000,
                    "description": "Max rows returned. GA4 caps at 250,000 per request.",
                    "condition": _cond_any("run_report", "run_realtime_report", "run_pivot_report"),
                    "mode": "advanced",
                },
                {
                    "name": "offset",
                    "label": "Row offset",
                    "type": "number",
                    "default": 0,
                    "condition": _cond_any("run_report", "run_pivot_report"),
                    "mode": "advanced",
                },
                {
                    "name": "dimension_filter",
                    "label": "Dimension filter (JSON)",
                    "type": "json",
                    "placeholder": (
                        '{ "filter": { "fieldName": "country", '
                        '"stringFilter": { "value": "United States" } } }'
                    ),
                    "description": (
                        "Forwarded verbatim as the API's `dimensionFilter`. "
                        "See Data API docs for the FilterExpression shape."
                    ),
                    "condition": _cond_any("run_report", "run_realtime_report", "run_pivot_report"),
                    "mode": "advanced",
                },
                {
                    "name": "metric_filter",
                    "label": "Metric filter (JSON)",
                    "type": "json",
                    "placeholder": (
                        '{ "filter": { "fieldName": "sessions", '
                        '"numericFilter": { "operation": "GREATER_THAN", '
                        '"value": { "int64Value": "10" } } } }'
                    ),
                    "condition": _cond_any("run_report", "run_pivot_report"),
                    "mode": "advanced",
                },
                {
                    "name": "order_by",
                    "label": "Order by (JSON array)",
                    "type": "json",
                    "placeholder": ('[ { "metric": { "metricName": "sessions" }, "desc": true } ]'),
                    "condition": _cond_any("run_report", "run_pivot_report"),
                    "mode": "advanced",
                },
                {
                    "name": "currency_code",
                    "label": "Currency",
                    "type": "string",
                    "placeholder": "USD",
                    "description": "ISO 4217 code for currency metrics.",
                    "condition": _cond_any("run_report", "run_pivot_report"),
                    "mode": "advanced",
                },
                {
                    "name": "keep_empty_rows",
                    "label": "Include empty rows",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("run_report"),
                    "mode": "advanced",
                },
                {
                    "name": "pivots",
                    "label": "Pivots (JSON array)",
                    "type": "json",
                    "required": True,
                    "placeholder": ('[ { "fieldNames": ["country"], "limit": 10 } ]'),
                    "description": "Each pivot is a `Pivot` per Data API docs.",
                    "condition": _cond("run_pivot_report"),
                },
                {
                    "name": "requests_body",
                    "label": "Batch requests (JSON)",
                    "type": "json",
                    "required": True,
                    "placeholder": (
                        '{ "requests": [ { "dimensions": [{"name":"country"}], '
                        '"metrics": [{"name":"activeUsers"}] } ] }'
                    ),
                    "description": (
                        "Full `BatchRunReportsRequest` body. Up to 5 reports per call."
                    ),
                    "condition": _cond("batch_run_reports"),
                },
                {
                    "name": "compatibility_filter",
                    "label": "Compatibility filter",
                    "type": "options",
                    "default": "",
                    "options": [
                        {"label": "All", "value": ""},
                        {"label": "Compatible only", "value": "COMPATIBLE"},
                        {"label": "Incompatible only", "value": "INCOMPATIBLE"},
                    ],
                    "condition": _cond("check_compatibility"),
                    "mode": "advanced",
                },
                # Paging
                {
                    "name": "page_size",
                    "label": "Page size",
                    "type": "number",
                    "default": 50,
                    "condition": _cond_any(
                        "list_accounts",
                        "list_properties",
                        "list_data_streams",
                        "list_key_events",
                        "list_custom_dimensions",
                        "list_custom_metrics",
                    ),
                    "mode": "advanced",
                },
                {
                    "name": "page_token",
                    "label": "Page token",
                    "type": "string",
                    "placeholder": "{{ $node('Google Analytics 4').nextPageToken }}",
                    "condition": _cond_any(
                        "list_accounts",
                        "list_properties",
                        "list_data_streams",
                        "list_key_events",
                        "list_custom_dimensions",
                        "list_custom_metrics",
                    ),
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "rows", "type": "array"},
                {"label": "rowCount", "type": "number"},
                {"label": "dimensionHeaders", "type": "array"},
                {"label": "metricHeaders", "type": "array"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=format_ga4_error(exc.response.status_code, exc.response.text),
            )
        except ValueError as exc:
            return NodeResult(success=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleAnalyticsNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── shared helpers ──────────────────────────────────────────────────────


def _require_property(node: GoogleAnalyticsNode) -> str | NodeResult:
    prop = (node.props.property or "").strip()
    if not prop:
        return NodeResult(success=False, error="Property is required.")
    return prop


def _require_account(node: GoogleAnalyticsNode) -> str | NodeResult:
    acc = (node.props.account or "").strip()
    if not acc:
        return NodeResult(success=False, error="Account is required.")
    return acc


def _build_paging_params(node: GoogleAnalyticsNode) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if node.props.page_size:
        params["pageSize"] = max(1, min(int(node.props.page_size), 200))
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    return params


def _build_report_body(node: GoogleAnalyticsNode, *, realtime: bool = False) -> dict[str, Any]:
    """Compose the Data API report body. Realtime reports skip the
    ``dateRanges`` field — they always cover the past 30 minutes."""
    metric_names = _parse_name_list(node.props.metrics)
    if not metric_names:
        raise ValueError("`metrics` is required — supply at least one metric name.")
    dimension_names = _parse_name_list(node.props.dimensions)

    body: dict[str, Any] = {
        "metrics": [{"name": m} for m in metric_names],
    }
    if dimension_names:
        body["dimensions"] = [{"name": d} for d in dimension_names]
    if not realtime:
        start = _normalise_date(node.props.start_date or "30daysAgo")
        end = _normalise_date(node.props.end_date or "today")
        body["dateRanges"] = [{"startDate": start, "endDate": end}]
    if node.props.limit:
        body["limit"] = int(node.props.limit)
    if node.props.offset:
        body["offset"] = int(node.props.offset)
    dim_filter = _coerce_json_field(node.props.dimension_filter)
    if dim_filter is not None:
        body["dimensionFilter"] = dim_filter
    metric_filter = _coerce_json_field(node.props.metric_filter)
    if metric_filter is not None:
        body["metricFilter"] = metric_filter
    order_by = _coerce_json_field(node.props.order_by)
    if order_by is not None:
        body["orderBys"] = order_by if isinstance(order_by, list) else [order_by]
    if node.props.currency_code:
        body["currencyCode"] = node.props.currency_code.strip().upper()
    if node.props.keep_empty_rows:
        body["keepEmptyRows"] = True
    return body


# ── handlers ────────────────────────────────────────────────────────────


async def _run_report(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    body = _build_report_body(node)
    r = await client.post(f"{DATA_API}/{prop}:runReport", headers=headers, json=body)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _run_realtime_report(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    body = _build_report_body(node, realtime=True)
    # Realtime API doesn't accept date ranges; double-check we stripped them.
    body.pop("dateRanges", None)
    r = await client.post(
        f"{DATA_API}/{prop}:runRealtimeReport",
        headers=headers,
        json=body,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _run_pivot_report(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    pivots = _coerce_json_field(node.props.pivots)
    if not isinstance(pivots, list) or not pivots:
        return NodeResult(success=False, error="`pivots` must be a non-empty JSON array.")
    body = _build_report_body(node)
    body["pivots"] = pivots
    r = await client.post(
        f"{DATA_API}/{prop}:runPivotReport",
        headers=headers,
        json=body,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _batch_run_reports(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    body = _coerce_json_field(node.props.requests_body)
    if not isinstance(body, dict) or "requests" not in body:
        return NodeResult(
            success=False,
            error="`requests_body` must be a JSON object with a `requests` array.",
        )
    r = await client.post(
        f"{DATA_API}/{prop}:batchRunReports",
        headers=headers,
        json=body,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _check_compatibility(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    metric_names = _parse_name_list(node.props.metrics)
    if not metric_names:
        return NodeResult(success=False, error="`metrics` is required.")
    dimension_names = _parse_name_list(node.props.dimensions)
    body: dict[str, Any] = {
        "metrics": [{"name": m} for m in metric_names],
    }
    if dimension_names:
        body["dimensions"] = [{"name": d} for d in dimension_names]
    filt = (node.props.compatibility_filter or "").strip()
    if filt:
        body["compatibilityFilter"] = filt
    r = await client.post(
        f"{DATA_API}/{prop}:checkCompatibility",
        headers=headers,
        json=body,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_metadata(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    r = await client.get(f"{DATA_API}/{prop}/metadata", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


# ── Admin API handlers ──────────────────────────────────────────────────


async def _list_accounts(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    params = _build_paging_params(node)
    r = await client.get(f"{ADMIN_API}/accounts", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_properties(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    """List properties under one account. Admin API requires a filter
    parameter on the top-level properties.list endpoint — we always
    scope by the supplied account."""
    acc = _require_account(node)
    if isinstance(acc, NodeResult):
        return acc
    params = _build_paging_params(node)
    params["filter"] = f"parent:{acc}"
    r = await client.get(f"{ADMIN_API}/properties", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_property(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    r = await client.get(f"{ADMIN_API}/{prop}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_data_streams(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    params = _build_paging_params(node)
    r = await client.get(
        f"{ADMIN_API}/{prop}/dataStreams",
        headers=headers,
        params=params,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_key_events(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    params = _build_paging_params(node)
    r = await client.get(
        f"{ADMIN_API}/{prop}/keyEvents",
        headers=headers,
        params=params,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_custom_dimensions(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    params = _build_paging_params(node)
    r = await client.get(
        f"{ADMIN_API}/{prop}/customDimensions",
        headers=headers,
        params=params,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_custom_metrics(
    node: GoogleAnalyticsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    prop = _require_property(node)
    if isinstance(prop, NodeResult):
        return prop
    params = _build_paging_params(node)
    r = await client.get(
        f"{ADMIN_API}/{prop}/customMetrics",
        headers=headers,
        params=params,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


_HANDLERS: dict[str, Any] = {
    "run_report": _run_report,
    "run_realtime_report": _run_realtime_report,
    "run_pivot_report": _run_pivot_report,
    "batch_run_reports": _batch_run_reports,
    "check_compatibility": _check_compatibility,
    "get_metadata": _get_metadata,
    "list_accounts": _list_accounts,
    "list_properties": _list_properties,
    "get_property": _get_property,
    "list_data_streams": _list_data_streams,
    "list_key_events": _list_key_events,
    "list_custom_dimensions": _list_custom_dimensions,
    "list_custom_metrics": _list_custom_metrics,
}

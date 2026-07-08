"""Google Search Console action node — one node, 10 operations.

Sites:
  - ``list_sites``  — verified properties the user can access
  - ``get_site``    — permission level for a single site
  - ``add_site``    — register a site (verification still required
    out-of-band via the Search Console UI)
  - ``delete_site`` — remove a site

Search analytics (the reporting workhorse):
  - ``query_search_analytics`` — clicks / impressions / ctr / position
    sliced by dimensions (query, page, country, device, date,
    searchAppearance), with optional row filters and result aggregation.

Sitemaps:
  - ``list_sitemaps``
  - ``get_sitemap``
  - ``submit_sitemap``
  - ``delete_sitemap``

URL inspection (v1 API surface):
  - ``inspect_url`` — full status snapshot of one URL: indexing,
    mobile usability, AMP, rich results.

OAuth scope: ``webmasters`` (added to GoogleOAuthProvider). The
narrower ``webmasters.readonly`` would lock users out of the sitemap
+ site-management writes — every workflow author who wants to ship
"refresh sitemap on publish" needs the full scope, so we ship one.

Notes from build
  - Search Console site URLs are NOT resource paths — they're literal
    URLs (``https://example.com/`` or ``sc-domain:example.com``). The
    picker emits the URL string verbatim and the runtime URL-encodes
    it inline at each endpoint.
  - The Search Analytics API caps rowLimit at 25,000; we forward
    whatever the user passes and let the API enforce.
  - URL inspection lives on the v1 API (``searchconsole.googleapis.com``),
    while site / sitemap / search-analytics still live on the v3
    Webmasters API. Both share the same scope.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.errors import make_structured_error
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

WEBMASTERS_API = "https://www.googleapis.com/webmasters/v3"
SEARCH_CONSOLE_API = "https://searchconsole.googleapis.com/v1"


def format_gsc_error(status_code: int, body: str) -> str:
    """Turn a Search Console API error into a structured error payload.

    Common setup gaps:
      * **403 PERMISSION_DENIED** — the connected account doesn't own
        the site, or the Search Console API isn't enabled in the GCP
        project hosting the OAuth client.
      * **404** — site URL wrong, or sitemap path wrong.
      * **400** — invalid search-analytics request body or unknown
        dimension / filter shape.

    Unhandled statuses fall through to a plain string so the default
    renderer keeps working.
    """
    snippet = (body or "").strip()[:600]
    lower = snippet.lower()

    if status_code == 403 and "permission" in lower:
        return make_structured_error(
            "Search Console rejected the request",
            summary=(
                "The connected Google account doesn't have access to "
                "this property in Search Console, or the Search Console "
                "API isn't enabled for the GCP project hosting the "
                "OAuth client."
            ),
            actions=[
                "Verify the property at search.google.com/search-console and confirm the connected Google account is listed under Settings → Users and permissions.",
                "GCP Console → APIs & Services → Library → enable `searchconsole.googleapis.com`.",
                "Disconnect + reconnect the Google credential to grant the `webmasters` scope if you connected before today.",
            ],
            raw=snippet,
        )

    if status_code == 404:
        return make_structured_error(
            "Search Console resource not found",
            summary=(
                "The site URL or sitemap path doesn't match anything the connected account can see."
            ),
            actions=[
                "Re-open the site picker and re-select the property.",
                "Verify the URL form — domain properties use `sc-domain:example.com`, URL-prefix properties use `https://example.com/` (note the trailing slash).",
                "For sitemaps, double-check the feedpath matches what's registered in Search Console.",
            ],
            raw=snippet,
        )

    if status_code == 400:
        return make_structured_error(
            "Search Console request invalid",
            summary=(
                "The API rejected the request body. Most often this "
                "means an unknown dimension / filter name on a search "
                "analytics query, or a malformed sitemap URL."
            ),
            actions=[
                "For `query_search_analytics`: dimensions must be `query`, `page`, `country`, `device`, `searchAppearance`, or `date`.",
                "Dimension filter operators: `equals`, `notEquals`, `contains`, `notContains`, `includingRegex`, `excludingRegex`.",
            ],
            raw=snippet,
        )

    if status_code == 429:
        return make_structured_error(
            "Search Console API quota exceeded",
            summary=(
                "The project ran out of Search Console quota for this "
                "window — typically 1,200 queries per minute per user. "
                "Calls resume once the quota refills."
            ),
            actions=[
                "Wait and retry — quota refills automatically.",
                "GCP Console → IAM & Admin → Quotas if you need a higher cap.",
            ],
            raw=snippet,
        )

    return f"Search Console API error {status_code}: {snippet or '(no body)'}"


def _to_site_url(raw: str) -> str:
    """Normalise a site identifier.

    Accepts:
      * URL-prefix form: ``https://example.com/`` (must end with `/`)
      * Domain-property form: ``sc-domain:example.com``
      * A bare hostname → assume URL-prefix with https + trailing slash.

    Returns the canonical form the API accepts. Leaves the more exotic
    forms alone so power users keep full control.
    """
    raw = raw.strip()
    if not raw:
        return raw
    if raw.startswith("sc-domain:"):
        return raw
    if raw.startswith(("http://", "https://")):
        return raw if raw.endswith("/") else raw + "/"
    # Bare hostname — default to https:// + trailing slash.
    return f"https://{raw.rstrip('/')}/"


def _coerce_json_field(raw: Any) -> Any:
    """Accept dict, list, or JSON string. Empty → None."""
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


def _parse_name_list(raw: Any) -> list[str]:
    """Comma-separated string OR JSON array → list[str]."""
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


_SEARCH_TYPE_OPTIONS: list[dict[str, str]] = [
    {"label": "Web (default)", "value": ""},
    {"label": "Web", "value": "web"},
    {"label": "Image", "value": "image"},
    {"label": "Video", "value": "video"},
    {"label": "News", "value": "news"},
    {"label": "Discover", "value": "discover"},
    {"label": "Google News", "value": "googleNews"},
]

_DATA_STATE_OPTIONS: list[dict[str, str]] = [
    {"label": "Final (default)", "value": ""},
    {"label": "Final", "value": "final"},
    {"label": "All (includes fresh / not yet finalised)", "value": "all"},
]


class GoogleSearchConsoleProperties(BaseModel):
    credential: str | None = None
    operation: str = "query_search_analytics"

    # Site identifier — literal URL or sc-domain: form.
    site: str | None = None

    # query_search_analytics
    start_date: str | None = None
    end_date: str | None = None
    dimensions: Any = None
    search_type: str | None = None
    data_state: str | None = None
    aggregation_type: str | None = None  # auto / byPage / byProperty
    dimension_filter_groups: Any = None  # full FilterGroups JSON
    row_limit: int | None = None
    start_row: int | None = None

    # sitemap ops
    feedpath: str | None = None  # sitemap URL

    # URL inspection
    inspection_url: str | None = None
    inspection_language_code: str | None = None  # e.g. "en-US"

    # Paging (sites + sitemaps don't paginate; reserved for future)
    page_size: int | None = None
    page_token: str | None = None

    @field_validator("site", mode="before")
    @classmethod
    def _coerce_site(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        if isinstance(value, dict):
            v = value.get("siteUrl") or value.get("id") or value.get("name") or ""
            if not v:
                return None
            return _to_site_url(str(v))
        return _to_site_url(str(value))


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GoogleSearchConsoleNode(BaseNode[GoogleSearchConsoleProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleSearchConsoleProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gsc",
            name="Google Search Console",
            category="integration",
            description=(
                "Query Search Console — pull clicks / impressions / "
                "CTR / position by query / page / country / device / "
                "date, manage sitemaps, inspect URL indexing status. "
                "Powered by the Webmasters v3 + Search Console v1 APIs."
            ),
            icon="google-search-console",
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
                    "default": "query_search_analytics",
                    "options": [
                        {"label": "Query search analytics", "value": "query_search_analytics"},
                        {"label": "Inspect URL", "value": "inspect_url"},
                        {"label": "List sites", "value": "list_sites"},
                        {"label": "Get site", "value": "get_site"},
                        {"label": "Add site", "value": "add_site"},
                        {"label": "Delete site", "value": "delete_site"},
                        {"label": "List sitemaps", "value": "list_sitemaps"},
                        {"label": "Get sitemap", "value": "get_sitemap"},
                        {"label": "Submit sitemap", "value": "submit_sitemap"},
                        {"label": "Delete sitemap", "value": "delete_sitemap"},
                    ],
                },
                {
                    "name": "site",
                    "label": "Site",
                    "type": "gsc-site",
                    "required": True,
                    "condition": _cond_any(
                        "query_search_analytics",
                        "inspect_url",
                        "get_site",
                        "list_sitemaps",
                        "get_sitemap",
                        "submit_sitemap",
                        "delete_sitemap",
                    ),
                },
                {
                    "name": "site",
                    "label": "Site URL",
                    "type": "string",
                    "required": True,
                    "placeholder": "https://example.com/  or  sc-domain:example.com",
                    "description": (
                        "URL-prefix form must include the trailing slash. "
                        "Domain properties use the `sc-domain:` prefix."
                    ),
                    "condition": _cond_any("add_site", "delete_site"),
                },
                # search analytics inputs
                {
                    "name": "start_date",
                    "label": "Start date",
                    "type": "string",
                    "required": True,
                    "default": "30daysAgo",
                    "placeholder": "30daysAgo  or  2024-01-01",
                    "description": (
                        "GSC accepts `YYYY-MM-DD` only — the API rejects "
                        "relative strings. We translate common shortcuts "
                        "(`today`, `yesterday`, `NdaysAgo`) before "
                        "sending."
                    ),
                    "condition": _cond("query_search_analytics"),
                },
                {
                    "name": "end_date",
                    "label": "End date",
                    "type": "string",
                    "required": True,
                    "default": "today",
                    "placeholder": "today  or  2024-12-31",
                    "condition": _cond("query_search_analytics"),
                },
                {
                    "name": "dimensions",
                    "label": "Dimensions",
                    "type": "string",
                    "placeholder": "query,page,country",
                    "description": (
                        "Comma-separated. Valid: `query`, `page`, `country`, "
                        "`device`, `searchAppearance`, `date`."
                    ),
                    "condition": _cond("query_search_analytics"),
                },
                {
                    "name": "search_type",
                    "label": "Search type",
                    "type": "options",
                    "default": "",
                    "options": _SEARCH_TYPE_OPTIONS,
                    "condition": _cond("query_search_analytics"),
                    "mode": "advanced",
                },
                {
                    "name": "data_state",
                    "label": "Data state",
                    "type": "options",
                    "default": "",
                    "options": _DATA_STATE_OPTIONS,
                    "description": (
                        "`all` includes fresh data that hasn't been "
                        "finalised yet — useful for last-48-hours dashboards."
                    ),
                    "condition": _cond("query_search_analytics"),
                    "mode": "advanced",
                },
                {
                    "name": "aggregation_type",
                    "label": "Aggregation",
                    "type": "options",
                    "default": "",
                    "options": [
                        {"label": "Auto (default)", "value": ""},
                        {"label": "By page", "value": "byPage"},
                        {"label": "By property", "value": "byProperty"},
                    ],
                    "condition": _cond("query_search_analytics"),
                    "mode": "advanced",
                },
                {
                    "name": "dimension_filter_groups",
                    "label": "Dimension filter groups (JSON)",
                    "type": "json",
                    "placeholder": (
                        '[ { "groupType": "and", "filters": [ '
                        '{ "dimension": "country", "operator": "equals", '
                        '"expression": "USA" } ] } ]'
                    ),
                    "description": (
                        "Forwarded verbatim. Each group's filters are AND-ed; "
                        "groups are OR-ed at the top level."
                    ),
                    "condition": _cond("query_search_analytics"),
                    "mode": "advanced",
                },
                {
                    "name": "row_limit",
                    "label": "Row limit",
                    "type": "number",
                    "default": 1000,
                    "description": "Max rows returned. API caps at 25,000.",
                    "condition": _cond("query_search_analytics"),
                    "mode": "advanced",
                },
                {
                    "name": "start_row",
                    "label": "Start row",
                    "type": "number",
                    "default": 0,
                    "condition": _cond("query_search_analytics"),
                    "mode": "advanced",
                },
                # sitemap inputs
                {
                    "name": "feedpath",
                    "label": "Sitemap URL",
                    "type": "string",
                    "required": True,
                    "placeholder": "https://example.com/sitemap.xml",
                    "condition": _cond_any(
                        "get_sitemap",
                        "submit_sitemap",
                        "delete_sitemap",
                    ),
                },
                # URL inspection
                {
                    "name": "inspection_url",
                    "label": "URL to inspect",
                    "type": "string",
                    "required": True,
                    "placeholder": "https://example.com/some/page",
                    "condition": _cond("inspect_url"),
                },
                {
                    "name": "inspection_language_code",
                    "label": "Language",
                    "type": "string",
                    "default": "en-US",
                    "placeholder": "en-US",
                    "description": "BCP-47 code. Drives the human-readable text in the response.",
                    "condition": _cond("inspect_url"),
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "rows", "type": "array"},
                {"label": "responseAggregationType", "type": "string"},
                {"label": "siteEntry", "type": "array"},
                {"label": "inspectionResult", "type": "object"},
                {"label": "sitemap", "type": "array"},
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
                error=format_gsc_error(exc.response.status_code, exc.response.text),
            )
        except ValueError as exc:
            return NodeResult(success=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleSearchConsoleNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── shared helpers ──────────────────────────────────────────────────────


def _require_site(node: GoogleSearchConsoleNode) -> str | NodeResult:
    site = (node.props.site or "").strip()
    if not site:
        return NodeResult(success=False, error="Site is required.")
    return site


def _site_path(site: str) -> str:
    """URL-encode the site for use as a path segment. `quote(safe="")`
    so `:` / `/` in the value get percent-encoded — `sc-domain:` becomes
    `sc-domain%3A`, which is what the API expects."""
    return quote(site, safe="")


_DATE_SHORTCUTS = {"today", "yesterday"}


def _normalise_date(raw: str) -> str:
    """The Search Analytics API only accepts ``YYYY-MM-DD`` — no
    relative strings. We translate the common ones up-front so the
    field stays ergonomic. Absolute dates pass through unchanged."""
    from datetime import UTC, datetime, timedelta

    raw = raw.strip()
    if not raw:
        return raw
    if len(raw) == 10 and raw[4] == "-" and raw[7] == "-":
        return raw

    today = datetime.now(UTC).date()
    lower = raw.lower()
    if lower == "today":
        return today.isoformat()
    if lower == "yesterday":
        return (today - timedelta(days=1)).isoformat()
    if lower.endswith("daysago") and lower[:-7].isdigit():
        n = int(lower[:-7])
        return (today - timedelta(days=n)).isoformat()
    # Unknown shape — let the API reject with a clear 400.
    return raw


# ── handlers ────────────────────────────────────────────────────────────


async def _query_search_analytics(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    start = _normalise_date(node.props.start_date or "30daysAgo")
    end = _normalise_date(node.props.end_date or "today")
    body: dict[str, Any] = {
        "startDate": start,
        "endDate": end,
    }
    dim_names = _parse_name_list(node.props.dimensions)
    if dim_names:
        body["dimensions"] = dim_names
    if node.props.search_type:
        body["type"] = node.props.search_type
    if node.props.data_state:
        body["dataState"] = node.props.data_state
    if node.props.aggregation_type:
        body["aggregationType"] = node.props.aggregation_type
    filt = _coerce_json_field(node.props.dimension_filter_groups)
    if filt is not None:
        body["dimensionFilterGroups"] = filt if isinstance(filt, list) else [filt]
    if node.props.row_limit:
        body["rowLimit"] = max(1, min(int(node.props.row_limit), 25000))
    if node.props.start_row:
        body["startRow"] = max(0, int(node.props.start_row))

    r = await client.post(
        f"{WEBMASTERS_API}/sites/{_site_path(site)}/searchAnalytics/query",
        headers=headers,
        json=body,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _inspect_url(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    target = (node.props.inspection_url or "").strip()
    if not target:
        return NodeResult(success=False, error="`inspection_url` is required.")
    body: dict[str, Any] = {
        "inspectionUrl": target,
        "siteUrl": site,
    }
    lang = (node.props.inspection_language_code or "").strip()
    if lang:
        body["languageCode"] = lang
    r = await client.post(
        f"{SEARCH_CONSOLE_API}/urlInspection/index:inspect",
        headers=headers,
        json=body,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _list_sites(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    r = await client.get(f"{WEBMASTERS_API}/sites", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_site(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    r = await client.get(f"{WEBMASTERS_API}/sites/{_site_path(site)}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _add_site(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    # PUT with no body — Search Console's "add site" is a PUT.
    r = await client.put(f"{WEBMASTERS_API}/sites/{_site_path(site)}", headers=headers)
    r.raise_for_status()
    # API returns 204; surface a confirmation so consumers have something
    # to log + a clean error pipeline if the call ever fails.
    return NodeResult(success=True, output_data={"site": site, "added": True})


async def _delete_site(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    r = await client.delete(f"{WEBMASTERS_API}/sites/{_site_path(site)}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data={"site": site, "deleted": True})


async def _list_sitemaps(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    r = await client.get(
        f"{WEBMASTERS_API}/sites/{_site_path(site)}/sitemaps",
        headers=headers,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_sitemap(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    feed = (node.props.feedpath or "").strip()
    if not feed:
        return NodeResult(success=False, error="`feedpath` is required.")
    r = await client.get(
        f"{WEBMASTERS_API}/sites/{_site_path(site)}/sitemaps/{_site_path(feed)}",
        headers=headers,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _submit_sitemap(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    feed = (node.props.feedpath or "").strip()
    if not feed:
        return NodeResult(success=False, error="`feedpath` is required.")
    r = await client.put(
        f"{WEBMASTERS_API}/sites/{_site_path(site)}/sitemaps/{_site_path(feed)}",
        headers=headers,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data={"feedpath": feed, "submitted": True})


async def _delete_sitemap(
    node: GoogleSearchConsoleNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    site = _require_site(node)
    if isinstance(site, NodeResult):
        return site
    feed = (node.props.feedpath or "").strip()
    if not feed:
        return NodeResult(success=False, error="`feedpath` is required.")
    r = await client.delete(
        f"{WEBMASTERS_API}/sites/{_site_path(site)}/sitemaps/{_site_path(feed)}",
        headers=headers,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data={"feedpath": feed, "deleted": True})


_HANDLERS: dict[str, Any] = {
    "query_search_analytics": _query_search_analytics,
    "inspect_url": _inspect_url,
    "list_sites": _list_sites,
    "get_site": _get_site,
    "add_site": _add_site,
    "delete_site": _delete_site,
    "list_sitemaps": _list_sitemaps,
    "get_sitemap": _get_sitemap,
    "submit_sitemap": _submit_sitemap,
    "delete_sitemap": _delete_sitemap,
}

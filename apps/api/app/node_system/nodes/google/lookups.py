"""Google brand-level remote-picker handlers.

One shared OAuth token authenticates every Google service, so all
Google pickers live here rather than under each sub-service folder.
Handlers hit Drive, Sheets, Calendar, Gmail, Cloud Storage, Tasks,
YouTube, Chat, Analytics, Search Console, and People with the
credential's `access_token`.

Existing bespoke pickers under `apps/api/app/features/credentials/
router.py` still work — this file adds the same resources under the
generic `/credentials/{id}/lookup/google/*` endpoint so manifest-driven
fields can share the pattern. Migration of the bespoke pickers to this
registry happens in a follow-up.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "google"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        raise ValueError("Google credential is missing access_token.")
    return {"Authorization": f"Bearer {token}"}


# ── Drive ──────────────────────────────────────────────────────────

_DRIVE = "https://www.googleapis.com/drive/v3"
_FOLDER_MIME = "application/vnd.google-apps.folder"


async def _drive_folders(client, cred, params, cursor, q):  # noqa: ANN001
    parent = (params.get("parent_id") or params.get("parent") or "root").strip() or "root"
    filters = [f"mimeType = '{_FOLDER_MIME}'", "trashed = false"]
    if parent != "any":
        filters.append(f"'{parent}' in parents")
    if q:
        filters.append(f"name contains '{q.replace(chr(39), chr(92) + chr(39))}'")
    r = await client.get(
        f"{_DRIVE}/files",
        headers=_headers(cred),
        params={
            "q": " and ".join(filters),
            "pageSize": 100,
            "fields": "nextPageToken,files(id,name)",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
            **({"pageToken": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [LookupItem(id=f["id"], label=f["name"]) for f in payload.get("files", [])]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


async def _drive_files(client, cred, params, cursor, q):  # noqa: ANN001
    mime = (params.get("mime_type") or "").strip()
    filters = ["trashed = false"]
    if mime:
        filters.append(f"mimeType = '{mime}'")
    if q:
        filters.append(f"name contains '{q.replace(chr(39), chr(92) + chr(39))}'")
    r = await client.get(
        f"{_DRIVE}/files",
        headers=_headers(cred),
        params={
            "q": " and ".join(filters),
            "pageSize": 100,
            "fields": "nextPageToken,files(id,name,mimeType)",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
            **({"pageToken": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=f["id"], label=f["name"], sublabel=f.get("mimeType"))
        for f in payload.get("files", [])
    ]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


# ── Sheets ─────────────────────────────────────────────────────────


async def _sheet_tabs(client, cred, params, _cursor, q):  # noqa: ANN001
    sid = (params.get("spreadsheet_id") or params.get("spreadsheet") or "").strip()
    if not sid:
        return LookupResponse(items=[])
    r = await client.get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{sid}",
        headers=_headers(cred),
        params={"fields": "sheets(properties(sheetId,title,index))"},
    )
    r.raise_for_status()
    sheets = r.json().get("sheets") or []
    items = [
        LookupItem(id=str(s["properties"]["title"]), label=s["properties"]["title"]) for s in sheets
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


# ── Calendar ───────────────────────────────────────────────────────


async def _calendars(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://www.googleapis.com/calendar/v3/users/me/calendarList",
        headers=_headers(cred),
        params={"maxResults": 100, **({"pageToken": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=c["id"], label=c.get("summary") or c["id"], sublabel=c.get("accessRole"))
        for c in payload.get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


# ── Gmail ──────────────────────────────────────────────────────────


async def _gmail_labels(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/labels",
        headers=_headers(cred),
    )
    r.raise_for_status()
    labels = r.json().get("labels", [])
    items = [LookupItem(id=lb["id"], label=lb["name"], sublabel=lb.get("type")) for lb in labels]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


# ── Cloud Storage ──────────────────────────────────────────────────


async def _gcs_buckets(client, cred, params, cursor, q):  # noqa: ANN001
    project = (params.get("project_id") or params.get("project") or "").strip()
    if not project:
        return LookupResponse(items=[])
    r = await client.get(
        "https://storage.googleapis.com/storage/v1/b",
        headers=_headers(cred),
        params={
            "project": project,
            "maxResults": 100,
            **({"pageToken": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=b["name"], label=b["name"], sublabel=b.get("location"))
        for b in payload.get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


# ── Tasks ──────────────────────────────────────────────────────────


async def _tasklists(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://tasks.googleapis.com/tasks/v1/users/@me/lists",
        headers=_headers(cred),
        params={"maxResults": 100, **({"pageToken": cursor} if cursor else {})},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(id=t["id"], label=t.get("title") or t["id"]) for t in payload.get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


# ── YouTube ────────────────────────────────────────────────────────


async def _yt_channels(client, cred, _params, _cursor, q):  # noqa: ANN001
    # Own channels — no search needed. Client-side filter handles `q`.
    r = await client.get(
        "https://youtube.googleapis.com/youtube/v3/channels",
        headers=_headers(cred),
        params={"part": "snippet", "mine": "true", "maxResults": 50},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=c["id"],
            label=(c.get("snippet") or {}).get("title") or c["id"],
            sublabel=(c.get("snippet") or {}).get("description") or None,
        )
        for c in r.json().get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _yt_playlists(client, cred, _params, cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://youtube.googleapis.com/youtube/v3/playlists",
        headers=_headers(cred),
        params={
            "part": "snippet",
            "mine": "true",
            "maxResults": 50,
            **({"pageToken": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=p["id"],
            label=(p.get("snippet") or {}).get("title") or p["id"],
        )
        for p in payload.get("items", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


# ── Chat ───────────────────────────────────────────────────────────


async def _chat_spaces(client, cred, params, cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://chat.googleapis.com/v1/spaces",
        headers=_headers(cred),
        params={
            "pageSize": 100,
            **(
                {"filter": f'spaceType = "{params["space_type"]}"'}
                if params.get("space_type")
                else {}
            ),
            **({"pageToken": cursor} if cursor else {}),
        },
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=s["name"],
            label=s.get("displayName") or s["name"],
            sublabel=s.get("spaceType"),
        )
        for s in payload.get("spaces", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    next_cursor = payload.get("nextPageToken")
    return LookupResponse(items=items, cursor=next_cursor, has_more=bool(next_cursor))


# ── GA4 ────────────────────────────────────────────────────────────


async def _ga4_properties(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
        headers=_headers(cred),
        params={"pageSize": 200},
    )
    r.raise_for_status()
    accounts = r.json().get("accountSummaries", [])
    items: list[LookupItem] = []
    for acct in accounts:
        acct_name = acct.get("displayName")
        for prop in acct.get("propertySummaries", []):
            items.append(
                LookupItem(
                    id=prop["property"],
                    label=prop.get("displayName") or prop["property"],
                    sublabel=acct_name,
                )
            )
    if q:
        needle = q.lower()
        items = [
            it
            for it in items
            if needle in it.label.lower() or needle in (it.sublabel or "").lower()
        ]
    return LookupResponse(items=items)


# ── Search Console ─────────────────────────────────────────────────


async def _gsc_sites(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://searchconsole.googleapis.com/webmasters/v3/sites",
        headers=_headers(cred),
    )
    r.raise_for_status()
    items = [
        LookupItem(id=s["siteUrl"], label=s["siteUrl"], sublabel=s.get("permissionLevel"))
        for s in r.json().get("siteEntry", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


# ── People / Contact Groups ────────────────────────────────────────


async def _people_groups(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(
        "https://people.googleapis.com/v1/contactGroups",
        headers=_headers(cred),
        params={"pageSize": 200},
    )
    r.raise_for_status()
    items = [
        LookupItem(
            id=g["resourceName"],
            label=g.get("formattedName") or g.get("name") or g["resourceName"],
            sublabel=g.get("groupType"),
        )
        for g in r.json().get("contactGroups", [])
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {
    "drive_folders": _drive_folders,
    "drive_files": _drive_files,
    "sheet_tabs": _sheet_tabs,
    "calendars": _calendars,
    "gmail_labels": _gmail_labels,
    "gcs_buckets": _gcs_buckets,
    "tasklists": _tasklists,
    "yt_channels": _yt_channels,
    "yt_playlists": _yt_playlists,
    "chat_spaces": _chat_spaces,
    "ga4_properties": _ga4_properties,
    "gsc_sites": _gsc_sites,
    "people_groups": _people_groups,
}

"""GitHub remote-picker handlers.

Powers `owner`, `repo`, and `branch` dropdowns on every GitHub-flavoured
node (see `manifest.py`). Each handler takes the decrypted OAuth
credential dict from `CredentialService` and hits `api.github.com` with
the user's `access_token`.

The registry key is the resource string on `FieldSpec.remote.resource`
— keep these stable, they're referenced from manifests.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "github"

_API = "https://api.github.com"
_PER_PAGE = 50


def _auth_headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token")
    if not token:
        # Handler-level 400s bubble up via HTTPX raising below when the
        # unauth'd call comes back — but a missing token is a config
        # bug, not a GitHub outage. Fail loud with a clear message.
        raise ValueError("GitHub credential is missing access_token.")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def _owners(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    _params: dict[str, str],
    _cursor: str | None,
    q: str | None,
) -> LookupResponse:
    """List the current user + every org the token can see. GitHub
    doesn't expose a combined 'accounts you can act on' endpoint, so
    we merge `/user` (personal account) with `/user/orgs`.
    """
    headers = _auth_headers(cred)
    user_r, orgs_r = (
        await client.get(f"{_API}/user", headers=headers),
        await client.get(f"{_API}/user/orgs", headers=headers, params={"per_page": _PER_PAGE}),
    )
    user_r.raise_for_status()
    orgs_r.raise_for_status()
    user = user_r.json()
    orgs = orgs_r.json()

    items: list[LookupItem] = []
    if user.get("login"):
        items.append(
            LookupItem(
                id=user["login"],
                label=user["login"],
                sublabel="Personal account",
                icon_slug=None,
            )
        )
    for o in orgs:
        items.append(
            LookupItem(
                id=o["login"],
                label=o["login"],
                sublabel=o.get("description") or "Organization",
            )
        )

    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]

    return LookupResponse(items=items)


async def _repos(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    params: dict[str, str],
    _cursor: str | None,
    q: str | None,
) -> LookupResponse:
    """List repositories under a given owner (user or org).

    When `owner` isn't supplied the picker returns nothing — the
    frontend surfaces "Set Owner first" for that state. This keeps the
    payload predictable and the handler simple.
    """
    owner = (params.get("owner") or "").strip()
    if not owner:
        return LookupResponse(items=[])

    headers = _auth_headers(cred)
    if q:
        # Search API is the only way to filter by name server-side.
        # `in:name` + `user:<owner>` scopes to that account's repos.
        search_r = await client.get(
            f"{_API}/search/repositories",
            headers=headers,
            params={"q": f"{q} in:name user:{owner}", "per_page": _PER_PAGE, "sort": "updated"},
        )
        search_r.raise_for_status()
        payload = search_r.json()
        items = [
            LookupItem(
                id=r["name"],
                label=r["name"],
                sublabel=r.get("description") or ("Private" if r.get("private") else "Public"),
            )
            for r in payload.get("items", [])
        ]
        return LookupResponse(items=items)

    # Try user endpoint first, fall back to org endpoint on 404 — we
    # don't know which one `owner` is upfront and it's cheap to probe.
    for path in (f"{_API}/users/{owner}/repos", f"{_API}/orgs/{owner}/repos"):
        r = await client.get(
            path, headers=headers, params={"per_page": _PER_PAGE, "sort": "updated"}
        )
        if r.status_code == 404:
            continue
        r.raise_for_status()
        payload = r.json()
        items = [
            LookupItem(
                id=repo["name"],
                label=repo["name"],
                sublabel=repo.get("description")
                or ("Private" if repo.get("private") else "Public"),
            )
            for repo in payload
        ]
        return LookupResponse(items=items)

    return LookupResponse(items=[])


async def _branches(
    client: httpx.AsyncClient,
    cred: dict[str, Any],
    params: dict[str, str],
    _cursor: str | None,
    q: str | None,
) -> LookupResponse:
    """List branches for `{owner}/{repo}`. Both must be provided —
    empty response otherwise. GitHub caps at 100/page which is plenty
    for the dropdown case.
    """
    owner = (params.get("owner") or "").strip()
    repo = (params.get("repo") or "").strip()
    if not owner or not repo:
        return LookupResponse(items=[])

    headers = _auth_headers(cred)
    r = await client.get(
        f"{_API}/repos/{owner}/{repo}/branches",
        headers=headers,
        params={"per_page": _PER_PAGE},
    )
    r.raise_for_status()
    payload = r.json()
    items = [
        LookupItem(
            id=b["name"],
            label=b["name"],
            sublabel="protected" if b.get("protected") else None,
        )
        for b in payload
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {
    "owners": _owners,
    "repos": _repos,
    "branches": _branches,
}

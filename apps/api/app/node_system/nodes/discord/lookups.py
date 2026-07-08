"""Discord remote-picker handlers — guilds (servers) + channels.

Discord is hand-written (custom BaseNode) so no manifest annotations
today, but the handlers stay ready for whenever those props migrate.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.features.credentials.lookups import LookupItem, LookupResponse

PROVIDER = "discord"

_API = "https://discord.com/api/v10"


def _headers(cred: dict[str, Any]) -> dict[str, str]:
    token = cred.get("access_token") or cred.get("bot_token") or cred.get("api_key")
    if not token:
        raise ValueError("Discord credential missing bot_token / access_token.")
    scheme = "Bot" if cred.get("bot_token") or cred.get("api_key") else "Bearer"
    return {"Authorization": f"{scheme} {token}"}


async def _guilds(client, cred, _params, _cursor, q):  # noqa: ANN001
    r = await client.get(f"{_API}/users/@me/guilds", headers=_headers(cred))
    r.raise_for_status()
    items = [
        LookupItem(id=g["id"], label=g.get("name") or g["id"], sublabel=g.get("id"))
        for g in r.json()
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


async def _channels(client, cred, params, _cursor, q):  # noqa: ANN001
    guild = (params.get("guild_id") or params.get("server_id") or "").strip()
    if not guild:
        return LookupResponse(items=[])
    r = await client.get(f"{_API}/guilds/{guild}/channels", headers=_headers(cred))
    r.raise_for_status()
    _CTYPES = {0: "text", 2: "voice", 4: "category", 5: "announcement", 15: "forum"}
    items = [
        LookupItem(
            id=c["id"],
            label=("#" if c.get("type") == 0 else "") + (c.get("name") or c["id"]),
            sublabel=_CTYPES.get(c.get("type"), str(c.get("type"))),
        )
        for c in r.json()
        if c.get("type") in _CTYPES
    ]
    if q:
        needle = q.lower()
        items = [it for it in items if needle in it.label.lower()]
    return LookupResponse(items=items)


LOOKUPS = {"guilds": _guilds, "channels": _channels}

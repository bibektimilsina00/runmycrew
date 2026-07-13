"""WebSocket auth transport that keeps the JWT out of the URL.

Browsers can't set arbitrary headers on a WebSocket handshake, but they
CAN offer subprotocols. So the token rides as a `Sec-WebSocket-Protocol`
value instead of `?token=<jwt>` — the latter lands in proxy/uvicorn
access logs and browser history.

Client offers two subprotocols: ``["fuse-auth", "<jwt>"]``. The server
reads the second and, when it authenticates, MUST echo the first back on
``accept(subprotocol="fuse-auth")`` or the browser fails the handshake.

The query param is still accepted as a fallback so an older frontend or a
non-browser client keeps working during the transition; new clients never
put the token in the URL.
"""

from __future__ import annotations

from starlette.websockets import WebSocket

_AUTH_SUBPROTOCOL = "fuse-auth"


def _offered_subprotocols(websocket: WebSocket) -> list[str]:
    raw = websocket.headers.get("sec-websocket-protocol")
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def ws_token(websocket: WebSocket, query_token: str | None) -> str | None:
    """Token from the subprotocol (preferred) or the query param (fallback)."""
    parts = _offered_subprotocols(websocket)
    if len(parts) >= 2 and parts[0] == _AUTH_SUBPROTOCOL:
        return parts[1]
    return query_token


def ws_accept_subprotocol(websocket: WebSocket) -> str | None:
    """The subprotocol to echo on ``accept()``. Returns ``"fuse-auth"``
    when the client used subprotocol auth (the handshake requires the
    server to select one of the offered protocols), else ``None`` for a
    plain accept."""
    parts = _offered_subprotocols(websocket)
    if parts and parts[0] == _AUTH_SUBPROTOCOL:
        return _AUTH_SUBPROTOCOL
    return None

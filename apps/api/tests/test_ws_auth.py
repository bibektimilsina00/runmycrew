"""WebSocket auth transport: token from the subprotocol (preferred) or
the query fallback, and the subprotocol the server must echo on accept.
Keeps the JWT out of the URL / access logs."""

from apps.api.app.core.ws_auth import ws_accept_subprotocol, ws_token


class _FakeWS:
    def __init__(self, protocol_header: str | None):
        self.headers = {}
        if protocol_header is not None:
            self.headers["sec-websocket-protocol"] = protocol_header


def test_token_from_subprotocol():
    ws = _FakeWS("fuse-auth, the.jwt.value")
    assert ws_token(ws, None) == "the.jwt.value"


def test_subprotocol_wins_over_query():
    ws = _FakeWS("fuse-auth, sub.token")
    assert ws_token(ws, "query.token") == "sub.token"


def test_falls_back_to_query_when_no_subprotocol():
    ws = _FakeWS(None)
    assert ws_token(ws, "query.token") == "query.token"


def test_falls_back_to_query_when_wrong_subprotocol():
    # A subprotocol that isn't our auth marker is ignored.
    ws = _FakeWS("graphql-ws")
    assert ws_token(ws, "query.token") == "query.token"


def test_none_when_nothing_provided():
    assert ws_token(_FakeWS(None), None) is None


def test_accept_subprotocol_echoes_only_for_auth_offer():
    assert ws_accept_subprotocol(_FakeWS("fuse-auth, jwt")) == "fuse-auth"
    assert ws_accept_subprotocol(_FakeWS("graphql-ws")) is None
    assert ws_accept_subprotocol(_FakeWS(None)) is None

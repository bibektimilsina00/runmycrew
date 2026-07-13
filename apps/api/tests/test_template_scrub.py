"""Template publish must strip inline secrets from the graph snapshot.

Credentials normally live as encrypted rows referenced by id, but a node
that stores a raw token/key inline would otherwise publish the
publisher's secret in plaintext for every installer. The scrub matches
credential ids AND common inline-secret property names across camelCase
and snake_case.
"""

from apps.api.app.features.templates.service import _prepare_graph_snapshot


def _graph(props: dict) -> dict:
    return {
        "nodes": [{"id": "n1", "type": "action.http_request", "data": {"properties": props}}],
        "edges": [],
    }


def _scrubbed_props(props: dict) -> dict:
    snapshot, _creds, _tools = _prepare_graph_snapshot(_graph(props))
    return snapshot["nodes"][0]["data"]["properties"]


def test_credential_id_blanked():
    out = _scrubbed_props({"credential": "cred-123", "url": "https://api.example.com"})
    assert out["credential"] == ""
    assert out["url"] == "https://api.example.com"  # non-secret untouched


def test_inline_secret_variants_blanked():
    secrets = {
        "apiKey": "sk-live-aaa",
        "api_key": "sk-live-bbb",
        "secretKey": "shh",
        "api_secret": "shh2",
        "bearerToken": "tok",
        "access_token": "tok2",
        "authToken": "tok3",
        "password": "hunter2",
        "privateKey": "-----BEGIN-----",
    }
    out = _scrubbed_props({**secrets, "method": "POST", "timeout": 30})
    for key in secrets:
        assert out[key] == "", f"{key} leaked through the scrub"
    # Non-secret props survive (and the int is untouched).
    assert out["method"] == "POST"
    assert out["timeout"] == 30


def test_non_string_secret_named_field_untouched():
    # max_tokens contains "token" but is an int config, not a secret.
    out = _scrubbed_props({"max_tokens": 4096})
    assert out["max_tokens"] == 4096

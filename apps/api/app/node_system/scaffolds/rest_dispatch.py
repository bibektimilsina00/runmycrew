"""Shared HTTP layer for the REST-tool scaffold.

Every manifest-built node hits the wire through `rest_request()`. We keep
the function thin on purpose — error framing, header assembly, and
response decoding are the only things that benefit from sharing. Per-op
logic stays on the factory side.

Mirrors what `github_helpers.github_request()` does for the GitHub node,
but generalized over auth scheme + content type. The two will likely
converge into this module in Phase 1.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.scaffolds.rest_manifest import (
    AuthScheme,
    ProviderManifest,
)


class RESTError(Exception):
    """Uniform error returned by `rest_request` on non-2xx responses.

    Carries the HTTP status, a best-effort error message, and the raw
    payload. The factory rethrows this as a `NodeResult(success=False)`
    so the workflow surfaces a clean, structured failure on the node's
    error port.
    """

    def __init__(self, status: int, message: str, payload: Any | None = None) -> None:
        super().__init__(f"{status}: {message}")
        self.status = status
        self.message = message
        self.payload = payload


def build_auth(
    *,
    token: str | None,
    scheme: AuthScheme,
    header_name: str,
    value_template: str,
    query_param: str,
    basic_username: str = "",
    credential: dict[str, Any] | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Return `(headers, query_params)` for the given auth scheme.

    Separated from `rest_request` so a custom handler can re-use the
    same logic without going through the generic call path — e.g. a
    GraphQL handler needs the same `Authorization` header but builds its
    own body.

    `basic_username` is consulted only for `scheme="basic"`. It may be:
      - empty string → legacy behavior, `{token}:` base64
      - a literal value (e.g. `"api"` for Mailgun) → `{value}:{token}`
      - a `{credential_key}` template → resolves against `credential`
        (e.g. `"{account_sid}"` for Twilio pulls the sid out of the
        credential dict)
    """

    if not token or scheme == "none":
        return {}, {}

    if scheme == "bearer":
        return {header_name: value_template.format(token=token)}, {}
    if scheme == "header_token":
        return {header_name: token}, {}
    if scheme == "basic":
        import base64
        import re as _re

        username = basic_username or ""
        if username and credential:
            # Resolve {credential_key} placeholders so the manifest can
            # name a credential field (e.g. `"{account_sid}"`).
            username = _re.sub(
                r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}",
                lambda m: str(credential.get(m.group(1), m.group(0))),
                username,
            )
        encoded = base64.b64encode(f"{username}:{token}".encode()).decode()
        return {header_name: f"Basic {encoded}"}, {}
    if scheme == "query_token":
        return {}, {query_param: token}

    return {}, {}


def error_from_response(resp: httpx.Response) -> RESTError:
    """Best-effort error extraction from a non-2xx response."""
    try:
        body = resp.json()
        message = (body.get("message") if isinstance(body, dict) else None) or resp.text[:300]
    except Exception:  # noqa: BLE001
        body = resp.text
        message = (resp.text or "")[:300]
    return RESTError(status=resp.status_code, message=message or "(no body)", payload=body)


async def rest_request(
    client: httpx.AsyncClient,
    *,
    method: str,
    url: str,
    manifest: ProviderManifest,
    token: str | None,
    params: dict[str, Any] | None = None,
    json: Any = None,
    credential: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, str]]:
    """Issue one HTTP call against a provider.

    `manifest` carries auth scheme + static headers; the rest are
    per-call. Returns `(parsed_body, response_headers)`. Raises
    `RESTError` on non-2xx so the factory can convert to a structured
    `NodeResult`.

    `credential` (the decrypted credential dict) is consulted only for
    advanced auth schemes that need a second field — e.g. Basic auth
    where the username is `{account_sid}` from the credential. It also
    flows into `extra_headers` templating so dual-header schemes can
    pull any credential field, not just `{token}`.
    """
    auth_headers, auth_params = build_auth(
        token=token,
        scheme=manifest.auth,
        header_name=manifest.auth_header_name,
        value_template=manifest.auth_value_template,
        query_param=manifest.auth_query_param,
        basic_username=manifest.auth_basic_username,
        credential=credential,
    )
    # `extra_headers` supports `{token}` plus any `{credential_key}`
    # placeholder. Lets providers that ride two custom headers (Sendblue
    # ships `sb-api-key-id` + `sb-api-secret-key`) declare both in the
    # manifest pulling distinct credential fields.
    resolved_extra: dict[str, str] = {}
    for k, v in manifest.extra_headers.items():
        if isinstance(v, str):
            value = v.replace("{token}", token or "") if token else v
            if credential:
                import re as _re

                value = _re.sub(
                    r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}",
                    lambda m: str(credential.get(m.group(1), m.group(0))),
                    value,
                )
            resolved_extra[k] = value
        else:
            resolved_extra[k] = v
    headers = {
        "Content-Type": manifest.content_type,
        "Accept": "application/json",
        **resolved_extra,
        **auth_headers,
    }
    merged_params: dict[str, Any] = {**auth_params, **(params or {})}

    # Form-encoded bodies — Twilio, Mailgun, and other legacy APIs
    # expect `application/x-www-form-urlencoded`. httpx routes those
    # through `data=`, not `json=`, so the keys land in the right wire
    # format.
    request_kwargs: dict[str, Any] = {
        "method": method,
        "url": url,
        "headers": headers,
        "params": merged_params or None,
        "timeout": manifest.timeout_seconds,
    }
    if manifest.content_type == "application/x-www-form-urlencoded":
        request_kwargs["data"] = json
    else:
        request_kwargs["json"] = json

    resp = await client.request(**request_kwargs)
    if resp.status_code >= 400:
        raise error_from_response(resp)

    body: Any
    if resp.status_code == 204 or not resp.content:
        body = None
    else:
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            body = resp.text
    return body, dict(resp.headers)


# ── flattener registry ────────────────────────────────────────────────


_FLATTENERS: dict[str, Any] = {}


def register_flatten(name: str, fn: Any) -> None:
    """Register a named output-flatten function.

    Manifests reference flatteners by name (`output_flatten="airtable.records"`)
    so a manifest stays pure-data — the actual callable lives next to the
    provider in its `__init__.py` or a `flatteners.py` file.
    """
    _FLATTENERS[name] = fn


def get_flatten(name: str | None) -> Any:
    if not name:
        return None
    return _FLATTENERS.get(name)

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

    if scheme == "aws_sigv4":
        # SigV4 needs the full request context (URL + body + query
        # params) so the real signing lands in `rest_request` after
        # body serialization. Return empty here; the outer flow will
        # stamp Authorization + X-Amz-* headers when it's ready.
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
    if scheme == "basic_token_only":
        # Token as username, empty password: `Basic base64(token:)`.
        # Greenhouse's Harvest API uses this; treating it as `basic`
        # would double the token when basic_username also resolves to
        # the api_key.
        import base64

        encoded = base64.b64encode(f"{token}:".encode()).decode()
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
    op_extra_headers: dict[str, str] | None = None,
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
    # Per-op headers layer on top of manifest-level extra_headers.
    # AWS JSON-protocol services (SQS, Athena, Secrets Manager) route
    # by X-Amz-Target: <Service>.<Action> — different per op — so this
    # is the only way to spell that without a custom handler per op.
    op_resolved: dict[str, str] = {}
    if op_extra_headers:
        for k, v in op_extra_headers.items():
            if isinstance(v, str):
                value = v.replace("{token}", token or "") if token else v
                if credential:
                    import re as _re

                    value = _re.sub(
                        r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}",
                        lambda m: str(credential.get(m.group(1), m.group(0))),
                        value,
                    )
                op_resolved[k] = value
            else:
                op_resolved[k] = v
    headers = {
        "Content-Type": manifest.content_type,
        "Accept": "application/json",
        **resolved_extra,
        **op_resolved,
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

    # AWS SigV4 signing runs after body serialization — the signer
    # needs the exact bytes going on the wire. Region + service come
    # from the manifest + credential; the signer stamps its own
    # X-Amz-Date, X-Amz-Content-Sha256, and Authorization headers.
    if manifest.auth == "aws_sigv4" and credential:
        import json as _json

        from apps.api.app.node_system.scaffolds.aws_signing import sign_v4

        body_bytes = b""
        if "json" in request_kwargs and request_kwargs["json"] is not None:
            body_bytes = _json.dumps(request_kwargs["json"]).encode("utf-8")
        elif "data" in request_kwargs and request_kwargs["data"] is not None:
            data_val = request_kwargs["data"]
            if isinstance(data_val, bytes | bytearray):
                body_bytes = bytes(data_val)
            elif isinstance(data_val, str):
                body_bytes = data_val.encode("utf-8")
            elif isinstance(data_val, dict):
                from urllib.parse import urlencode

                body_bytes = urlencode(data_val).encode("utf-8")
        region = (credential.get("region") if credential else None) or manifest.aws_default_region
        access_key = credential.get("access_key_id") or credential.get("aws_access_key_id") or ""
        secret_key = (
            credential.get("secret_access_key")
            or credential.get("aws_secret_access_key")
            or token
            or ""
        )
        session_token = credential.get("session_token") or credential.get("aws_session_token")
        signed = sign_v4(
            method=method,
            url=url,
            headers=headers,
            query_params=merged_params or None,
            body=body_bytes,
            region=region,
            service=manifest.aws_service or "",
            access_key=access_key,
            secret_key=secret_key,
            session_token=session_token,
            unsigned_payload=manifest.aws_unsigned_payload,
        )
        # Overwrite the placeholder Authorization built by `build_auth`
        # (which returned empty for `aws_sigv4`) with the SigV4 value.
        headers.update(signed)
        request_kwargs["headers"] = headers

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

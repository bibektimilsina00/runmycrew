"""AWS Signature Version 4 request signer.

Isolated from `rest_dispatch` so the SigV4 mechanics — canonical
request build, string-to-sign, HMAC chain, Authorization header —
stay in one testable file. `rest_request` calls `sign_v4` when the
manifest declares `auth="aws_sigv4"`.

Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html

The full request (method + URL + headers + body) has to be signed,
so this can't live inside `build_auth` — the auth headers depend on
what the wire request will look like. Signer runs after body
serialization, right before the `client.request(...)` call.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote, urlparse

_ALGO = "AWS4-HMAC-SHA256"
_UNSIGNED = "UNSIGNED-PAYLOAD"


def _hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _derive_signing_key(secret: str, date: str, region: str, service: str) -> bytes:
    """AWS-recommended HMAC chain that produces the signing key."""
    k_date = _hmac(("AWS4" + secret).encode("utf-8"), date)
    k_region = _hmac(k_date, region)
    k_service = _hmac(k_region, service)
    return _hmac(k_service, "aws4_request")


def _canonical_query(query_params: dict[str, Any] | None) -> str:
    """URI-encode + sort query params per SigV4 rules."""
    if not query_params:
        return ""
    # `quote(safe="")` matches AWS's insistence on percent-encoding
    # everything except unreserved chars.
    pairs = []
    for key in sorted(query_params.keys()):
        value = query_params[key]
        if isinstance(value, list):
            # SigV4 treats each list element as a repeated param.
            for v in value:
                pairs.append((str(key), str(v)))
        else:
            pairs.append((str(key), str(value if value is not None else "")))
    encoded = [f"{quote(k, safe='-_.~')}={quote(v, safe='-_.~')}" for k, v in pairs]
    return "&".join(encoded)


def _canonical_headers(headers: dict[str, str]) -> tuple[str, str]:
    """Return `(canonical_headers, signed_headers)` per SigV4."""
    normalized: dict[str, str] = {}
    for name, value in headers.items():
        lname = name.lower().strip()
        # Collapse internal whitespace runs to a single space, as SigV4
        # requires. Trim value edges.
        lvalue = " ".join(str(value).split())
        normalized[lname] = lvalue
    signed_names = sorted(normalized.keys())
    canonical = "".join(f"{n}:{normalized[n]}\n" for n in signed_names)
    return canonical, ";".join(signed_names)


def sign_v4(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    query_params: dict[str, Any] | None,
    body: bytes,
    region: str,
    service: str,
    access_key: str,
    secret_key: str,
    session_token: str | None = None,
    unsigned_payload: bool = False,
) -> dict[str, str]:
    """Sign one request. Returns the headers to *add* (or replace) on
    the outgoing request: `X-Amz-Date`, `X-Amz-Content-Sha256`,
    `Authorization`, and optionally `X-Amz-Security-Token`.

    `unsigned_payload=True` sets `X-Amz-Content-Sha256: UNSIGNED-PAYLOAD` —
    useful for large S3 uploads where hashing the body would double
    memory. Off by default; SigV4 with a payload hash is safer.
    """
    parsed = urlparse(url)
    canonical_uri = quote(parsed.path or "/", safe="/-_.~")
    canonical_query = _canonical_query(query_params)

    now = datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_scope = now.strftime("%Y%m%d")

    payload_hash = _UNSIGNED if unsigned_payload else _hash(body or b"")

    # Assemble the headers we're going to sign. Host is required.
    signed_headers_input: dict[str, str] = {
        "host": parsed.netloc,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        **{k: v for k, v in headers.items() if k.lower() not in {"authorization"}},
    }
    if session_token:
        signed_headers_input["x-amz-security-token"] = session_token

    canonical_headers, signed_headers = _canonical_headers(signed_headers_input)

    canonical_request = "\n".join(
        [
            method.upper(),
            canonical_uri,
            canonical_query,
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )
    credential_scope = f"{date_scope}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        [
            _ALGO,
            amz_date,
            credential_scope,
            _hash(canonical_request.encode("utf-8")),
        ]
    )

    signing_key = _derive_signing_key(secret_key, date_scope, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"{_ALGO} "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    result = {
        "Authorization": authorization,
        "X-Amz-Date": amz_date,
        "X-Amz-Content-Sha256": payload_hash,
    }
    if session_token:
        result["X-Amz-Security-Token"] = session_token
    return result


__all__ = ["sign_v4"]

"""Shared lookup helpers for Meta action nodes.

Two credential types feed Instagram nodes:

  - `meta_oauth` — Facebook Login for Business. Authorizes a User, a set
    of Pages, and (when linked) the IG Business account hanging off each
    Page. IG calls hit `graph.facebook.com` using the *page* access token.

  - `instagram_oauth` — standalone Instagram Login. Authorizes a single
    IG Business / Creator account directly, no Facebook Page. IG calls
    hit `graph.instagram.com` using the *IG user* access token.

`ig_send_context()` collapses the two into one return shape so each node
body stays focused on its API call.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.core.config import settings
from apps.api.app.node_system.base.node_result import NodeResult

# Credential types that can supply an Instagram account. Order matters
# only for the fallback path in `find_credential` (first match wins).
IG_CREDENTIAL_TYPES: tuple[str, ...] = ("meta_oauth", "instagram_oauth")


def require_webhook_payload(
    input_data: dict[str, Any],
    *,
    trigger_label: str,
) -> NodeResult | None:
    """Guard a Meta webhook trigger against being invoked with no payload.

    Trigger nodes only have meaning when fired by a real webhook delivery
    (the payload arrives via `MetaService.receive_webhook` → engine →
    `input_data = {object, field, target_id, value, received_at}`).
    A manual workflow run from the editor passes `input_data = {}`, which
    would otherwise yield a success with all-empty-strings output and
    mislead the user.

    Returns a failed `NodeResult` when the payload is missing, otherwise
    `None` so the caller can continue.
    """
    if not isinstance(input_data, dict) or not input_data.get("value"):
        return NodeResult(
            success=False,
            error=(
                f"{trigger_label} requires a webhook payload. This trigger "
                "fires when Meta delivers an event — it cannot be run manually "
                "without a sample event. Send a real interaction (comment, DM, "
                "etc.) on the connected account to test it."
            ),
        )
    return None


def resolve_media_field(value: Any) -> str | None:
    """Normalize a `media` field's stored value into a public URL.

    The MediaRenderer in the inspector saves one of two shapes:

      - Plain string URL — legacy / typed-in form, used as-is.
      - `{"type": "url", "value": "https://..."}` — same as above, just
        explicit. Use the `value` field.
      - `{"type": "asset", "asset_id": "<uuid>", ...}` — references a file
        in this workspace's Assets store. We mint a short-lived HMAC-signed
        public URL so Meta's content-publishing endpoint (which has no way
        to pass our auth header) can fetch it.

    Returns the resolved URL, or `None` when the field was empty / shaped
    wrong.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if not isinstance(value, dict):
        return None
    kind = str(value.get("type") or "").lower()
    if kind == "url":
        raw = value.get("value") or value.get("url") or ""
        return str(raw).strip() or None
    if kind == "asset":
        asset_id = value.get("asset_id") or value.get("id")
        if not asset_id:
            return None
        try:
            import uuid as _uuid

            from apps.api.app.features.assets.router import sign_public_asset_url
        except Exception:  # noqa: BLE001
            return None
        try:
            signed_path = sign_public_asset_url(_uuid.UUID(str(asset_id)))
        except (ValueError, TypeError):
            return None
        base = str(getattr(settings, "PUBLIC_BASE_URL", None) or settings.BASE_URL or "").rstrip(
            "/"
        )
        if not base:
            return signed_path
        return f"{base}{signed_path}"
    return None


def find_credential(
    credentials: list[dict[str, Any]] | None,
    selected_id: str | None,
    type_name: str | tuple[str, ...] = "meta_oauth",
) -> dict[str, Any] | None:
    """Pick the user-selected credential by id, falling back to the first
    credential of the given type when no explicit selection is set.

    `type_name` may be a single string or a tuple of accepted types.
    """
    creds = credentials or []
    accepted = (type_name,) if isinstance(type_name, str) else type_name
    if selected_id:
        match = next((c for c in creds if str(c.get("id")) == selected_id), None)
        if match is not None:
            return match
    return next((c for c in creds if c.get("type") in accepted), None)


def page_token_by_page_id(
    credential_data: dict[str, Any],
    page_id: str,
) -> str | None:
    """Return the non-expiring page access token for a given FB Page id, or
    None if the user no longer manages that Page through this credential."""
    pages = credential_data.get("pages")
    if not isinstance(pages, list):
        return None
    for page in pages:
        if not isinstance(page, dict):
            continue
        if str(page.get("id") or "") != page_id:
            continue
        token = page.get("access_token")
        if isinstance(token, str) and token:
            return token
    return None


def page_token_by_ig_account_id(
    credential_data: dict[str, Any],
    ig_account_id: str,
) -> str | None:
    """Return the page access token that owns the given IG business account.

    The OAuth callback enriches each page with
    `instagram_business_account.{id, username}` so this lookup avoids an
    extra Graph API hop on the hot path.

    Only applies to `meta_oauth` credentials. For `instagram_oauth`,
    use `ig_send_context()` instead.
    """
    pages = credential_data.get("pages")
    if not isinstance(pages, list):
        return None
    for page in pages:
        if not isinstance(page, dict):
            continue
        ig = page.get("instagram_business_account") or {}
        if str(ig.get("id") or "") != ig_account_id:
            continue
        token = page.get("access_token")
        if isinstance(token, str) and token:
            return token
    return None


def ig_send_context(
    credential: dict[str, Any],
    ig_account_id: str,
) -> tuple[str, str, str] | None:
    """Resolve (access_token, graph_base_url, ig_user_id) for an IG action.

    Branches on credential type:
      - `meta_oauth`: returns the page access token + graph.facebook.com.
        `ig_user_id` is the IG business account id supplied by the caller
        (must match a page's `instagram_business_account.id`).
      - `instagram_oauth`: returns the IG user access token +
        graph.instagram.com. `ig_user_id` is taken from the credential's
        stored ig_accounts[]; the caller's `ig_account_id` is checked
        against it for safety, but a mismatch is allowed (single-account
        credentials never differ at runtime).

    Returns None when no usable token can be derived.
    """
    if not isinstance(credential, dict):
        return None
    cred_type = credential.get("type")
    data = credential.get("data")
    if not isinstance(data, dict):
        return None
    version = settings.META_GRAPH_API_VERSION

    if cred_type == "instagram_oauth":
        accounts = data.get("ig_accounts") or []
        if not isinstance(accounts, list) or not accounts:
            return None
        # IG Login credentials authorize exactly one IG account. Use it
        # unless the caller selected a different id — in which case fall
        # through to None so the error message points at the mismatch.
        target = None
        for acc in accounts:
            if not isinstance(acc, dict):
                continue
            if not ig_account_id or str(acc.get("id") or "") == ig_account_id:
                target = acc
                break
        if target is None:
            return None
        token = target.get("access_token") or data.get("access_token")
        if not isinstance(token, str) or not token:
            return None
        return (
            token,
            f"https://graph.instagram.com/{version}",
            str(target.get("id") or ig_account_id),
        )

    # meta_oauth (default).
    token = page_token_by_ig_account_id(data, ig_account_id)
    if not token:
        return None
    return token, f"https://graph.facebook.com/{version}", ig_account_id

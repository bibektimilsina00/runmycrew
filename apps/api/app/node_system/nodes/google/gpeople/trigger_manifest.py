"""Google Contacts polling trigger — manifest form.

Two events, two cursor strategies:

  - `contact_added` — fires when a new contact appears in My Contacts.
    Cursor = known set of `resourceName`s. First poll snapshots; later
    polls diff against the set.
  - `contact_updated` — fires when an existing contact's `etag` changes.
    Cursor = `{resource_name: etag}` map. First poll snapshots; later
    polls emit on each mismatch.

The `etag` cursor doesn't fit the scaffold's three builtin strategies
(known_ids / since_timestamp / last_sha), so `contact_updated` registers
a `diff_handler` instead. Everything else — credential resolution,
scheduler binding, prop validation, inspector schema — comes free from
the polling scaffold.

`paginate_fn` walks every page of `people/me/connections` since
gpeople's polling needs the *full* contact list to detect deletions /
mid-list updates, not just the most recent page.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.nodes.google.gpeople import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.nodes.google.gpeople.gpeople_node import _flatten_contact
from apps.api.app.node_system.scaffolds import (
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)

PEOPLE_API = "https://people.googleapis.com/v1"
_POLL_PERSON_FIELDS = "names,emailAddresses,phoneNumbers,organizations,metadata"

register_flatten("gpeople.contact", _flatten_contact)


# ── custom paginator ─────────────────────────────────────────────────


async def _walk_connections(
    client: httpx.AsyncClient,
    *,
    manifest: PollingTriggerManifest,
    event: PollingEvent,
    token: str | None,
    props: Any,  # noqa: ARG001 — required by paginate_fn signature
) -> list[dict[str, Any]]:
    """Walk every page of `people/me/connections` up to 1000 entries.

    The scaffold's default fetcher does one page only; gpeople needs
    the full list so the etag-map diff can detect deletions and
    mid-list updates without false positives.
    """
    out: list[dict[str, Any]] = []
    page_token: str | None = None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    while True:
        params: dict[str, Any] = {
            "personFields": _POLL_PERSON_FIELDS,
            "pageSize": 1000,
            "sortOrder": "LAST_MODIFIED_DESCENDING",
        }
        if page_token:
            params["pageToken"] = page_token
        resp = await client.get(
            f"{PEOPLE_API}/people/me/connections",
            headers=headers,
            params=params,
            timeout=manifest.timeout_seconds,
        )
        resp.raise_for_status()
        data = resp.json() or {}
        out.extend(data.get("connections") or [])
        page_token = data.get("nextPageToken")
        if not page_token or len(out) >= 1000:
            break
    return out[:1000]


# ── custom diff for contact_updated (etag-map cursor) ────────────────


def _diff_contact_updated(
    items: list[dict[str, Any]],
    cursor: dict[str, Any] | None,
    props: Any,
    event_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Emit on every `etag` mismatch since last poll.

    First poll persists `{resource_name: etag}` for every contact and
    emits nothing — workflows should only fire on changes that arrive
    *after* the trigger was wired.

    On subsequent polls:
    - Skip contacts whose `resource_name` wasn't in prior (those are
      `contact_added` material, not updates).
    - Emit any contact whose current etag differs from prior.
    - Advance prior etags for emitted contacts only; defer the rest so
      a later poll has a chance to re-emit if the cursor was capped.
    """
    cap_raw = getattr(props, "max_per_poll", None)
    try:
        cap = max(1, min(int(cap_raw or 25), 500))
    except (TypeError, ValueError):
        cap = 25

    now_etags: dict[str, str] = {
        str(p.get("resourceName")): str(p.get("etag") or "") for p in items if p.get("resourceName")
    }
    prior = (cursor or {}).get("etags")
    if not isinstance(prior, dict):
        return [], {"event_type": event_id, "etags": now_etags}

    matches: list[dict[str, Any]] = []
    emitted: set[str] = set()
    for contact in items:
        resource_name = str(contact.get("resourceName") or "")
        now_tag = now_etags.get(resource_name, "")
        prior_tag = prior.get(resource_name)
        if prior_tag is None or not now_tag:
            # New contact (handled by contact_added) — record silently
            # so a later edit fires this event.
            continue
        if now_tag != prior_tag:
            matches.append({**_flatten_contact(contact), "event_type": event_id})
            emitted.add(resource_name)
            if len(matches) >= cap:
                break

    # Advance only emitted contacts; new arrivals get recorded so a
    # follow-up update fires; pre-existing untouched ones keep prior
    # tag so we don't lose the diff state.
    next_etags = dict(prior)
    for rn, tag in now_etags.items():
        if rn in emitted or rn not in prior:
            next_etags[rn] = tag

    return matches, {"event_type": event_id, "etags": next_etags}


# ── manifest ─────────────────────────────────────────────────────────


MANIFEST = PollingTriggerManifest(
    type="trigger.gpeople_change",
    name=NAME,
    category="trigger",
    description=(
        "Fires when contacts are added to or updated in your Google "
        "Contacts. First poll snapshots silently; later polls emit "
        "one execution per matching contact."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url=PEOPLE_API,
    credential_type="google_oauth",
    token_field=["access_token"],
    auth="bearer",
    provider="google_people",
    default_poll_interval_seconds=60,
    common_fields=[],
    events=[
        PollingEvent(
            id="contact_added",
            label="Contact added",
            list_path="/people/me/connections",
            strategy="known_ids",
            id_field="resourceName",
            flatten="gpeople.contact",
        ),
        PollingEvent(
            id="contact_updated",
            label="Contact updated",
            list_path="/people/me/connections",
            diff_handler=_diff_contact_updated,
        ),
    ],
    outputs_schema=[
        {"label": "resource_name", "type": "string"},
        {"label": "display_name", "type": "string"},
        {"label": "emails", "type": "array"},
        {"label": "phones", "type": "array"},
        {"label": "event_type", "type": "string"},
    ],
    paginate_fn=_walk_connections,
)

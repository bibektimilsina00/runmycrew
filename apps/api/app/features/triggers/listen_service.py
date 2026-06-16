"""Listen-slot store for "Listen for next event" debug runs.

Mirrors n8n's listen-for-test-event UX: the editor opens a single-shot
slot tied to a workflow's trigger node, the UI sits in a "Waiting…"
state, the next matching real webhook delivery routes through the slot
(fires the workflow once with the live payload, closes the slot), and
the canvas animates the trigger → action chain.

State lives in Redis with a TTL so a forgotten listen call eventually
drops itself. Slots index by `(object_type, target_id, field)` because
that is the routing tuple the webhook receiver already lifts off Meta's
envelope — keeps the matching logic O(1) with the existing flow.

A slot does NOT suppress production webhook dispatch. If the workflow is
also activated, the same event fires both the slot's execution and the
normal subscription-driven execution. That's intentional: the listen
slot is a debugging mirror, not a routing override.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from apps.api.app.core.logger import get_logger
from apps.api.app.core.redis import get_redis

logger = get_logger(__name__)

# Redis keyspace.
#   meta:listen:slot:{workflow_id}:{node_id}   — slot payload (one per node)
#   meta:listen:index:{object_type}:{target_id}:{field} — set of slot keys
# The set lets the webhook receiver list all slots matching a given
# routing tuple without scanning every key.
_SLOT_PREFIX = "meta:listen:slot"
_INDEX_PREFIX = "meta:listen:index"

DEFAULT_TTL_SECONDS = 5 * 60  # 5 minutes — matches n8n's default.


@dataclass(frozen=True)
class ListenSlot:
    workflow_id: str
    node_id: str
    execution_id: str
    object_type: str
    target_id: str
    field: str
    # Credential whose account-set the slot is bound to. Carried into the
    # slot so the webhook receiver can run a cred-aware id-namespace
    # fallback when Meta delivers an event under a different id than the
    # one used to register the slot (Instagram exposes 3 distinct ids per
    # account — Login-scoped, IG Graph, Messaging-scoped — and webhooks
    # don't always pick the one we registered with).
    credential_id: str = ""

    def slot_key(self) -> str:
        return f"{_SLOT_PREFIX}:{self.workflow_id}:{self.node_id}"

    @staticmethod
    def index_key(object_type: str, target_id: str, field: str) -> str:
        return f"{_INDEX_PREFIX}:{object_type}:{target_id}:{field}"

    def as_dict(self) -> dict[str, str]:
        return {
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "execution_id": self.execution_id,
            "object_type": self.object_type,
            "target_id": self.target_id,
            "field": self.field,
            "credential_id": self.credential_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ListenSlot:
        return cls(
            workflow_id=data["workflow_id"],
            node_id=data["node_id"],
            execution_id=data["execution_id"],
            object_type=data["object_type"],
            target_id=data["target_id"],
            field=data["field"],
            credential_id=str(data.get("credential_id") or ""),
        )


async def open_slot(slot: ListenSlot, ttl: int = DEFAULT_TTL_SECONDS) -> None:
    """Register a new listen slot. Overwrites any prior slot for the same
    (workflow, node) — only one debug listen per node at a time."""
    redis = await get_redis()
    existing_raw = await redis.get(slot.slot_key())
    if existing_raw:
        try:
            existing = json.loads(existing_raw)
            await redis.srem(
                ListenSlot.index_key(
                    existing["object_type"], existing["target_id"], existing["field"]
                ),
                slot.slot_key(),
            )
        except Exception:  # noqa: BLE001
            pass
    await redis.set(slot.slot_key(), json.dumps(slot.as_dict()), ex=ttl)
    index_key = ListenSlot.index_key(slot.object_type, slot.target_id, slot.field)
    await redis.sadd(index_key, slot.slot_key())
    await redis.expire(index_key, ttl + 60)


async def close_slot(workflow_id: str, node_id: str) -> ListenSlot | None:
    """Remove a slot. Returns the closed slot so the caller can log /
    mark its execution as cancelled."""
    redis = await get_redis()
    key = f"{_SLOT_PREFIX}:{workflow_id}:{node_id}"
    raw = await redis.get(key)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        await redis.delete(key)
        return None
    slot = ListenSlot.from_dict(data)
    await redis.delete(key)
    await redis.srem(
        ListenSlot.index_key(slot.object_type, slot.target_id, slot.field),
        key,
    )
    return slot


async def claim_slots_for_event(
    object_type: str,
    target_id: str,
    field: str,
) -> list[ListenSlot]:
    """Atomically claim every slot waiting on this (object, target, field).

    Each returned slot has been removed from Redis so the caller can fire
    it exactly once. Concurrent calls observe disjoint slot sets.
    """
    redis = await get_redis()
    index_key = ListenSlot.index_key(object_type, target_id, field)
    slot_keys = await redis.smembers(index_key)
    if not slot_keys:
        return []

    claimed: list[ListenSlot] = []
    for slot_key in slot_keys:
        raw = await redis.get(slot_key)
        if not raw:
            await redis.srem(index_key, slot_key)
            continue
        try:
            data = json.loads(raw)
        except Exception:  # noqa: BLE001
            await redis.delete(slot_key)
            await redis.srem(index_key, slot_key)
            continue
        # Single-shot semantics — drop the slot before fanning it out.
        await redis.delete(slot_key)
        await redis.srem(index_key, slot_key)
        try:
            claimed.append(ListenSlot.from_dict(data))
        except KeyError as exc:
            logger.warning(f"Malformed listen slot {slot_key!r}: missing {exc}")
    return claimed


async def list_slots_for_event(
    object_type: str,
    field: str,
) -> list[ListenSlot]:
    """Read every open slot for (object_type, field) WITHOUT claiming.

    The caller decides which slots are actually applicable to the current
    webhook (e.g. via a credential-aware id-namespace check) and then
    claims the matching ones via `claim_slot`. Slots that turn out not to
    apply stay in Redis and continue waiting.
    """
    redis = await get_redis()
    pattern = f"{_INDEX_PREFIX}:{object_type}:*:{field}"
    found: list[ListenSlot] = []
    async for index_key in redis.scan_iter(match=pattern):
        slot_keys = await redis.smembers(index_key)
        for slot_key in slot_keys:
            raw = await redis.get(slot_key)
            if not raw:
                await redis.srem(index_key, slot_key)
                continue
            try:
                data = json.loads(raw)
            except Exception:  # noqa: BLE001
                await redis.delete(slot_key)
                await redis.srem(index_key, slot_key)
                continue
            try:
                found.append(ListenSlot.from_dict(data))
            except KeyError as exc:
                logger.warning(f"Malformed listen slot {slot_key!r}: missing {exc}")
    return found


async def claim_slot(slot: ListenSlot) -> bool:
    """Atomically remove a single slot. Returns True iff this caller is
    the one that actually popped it (a concurrent webhook could have
    claimed it microseconds earlier — that race must be honoured because
    listen slots have single-shot semantics).
    """
    redis = await get_redis()
    slot_key = slot.slot_key()
    index_key = ListenSlot.index_key(slot.object_type, slot.target_id, slot.field)
    deleted = await redis.delete(slot_key)
    await redis.srem(index_key, slot_key)
    return bool(deleted)


async def find_slot(workflow_id: str, node_id: str) -> ListenSlot | None:
    """Read a slot without consuming it. Used by the cancel endpoint and
    by `/listen/status`."""
    redis = await get_redis()
    raw = await redis.get(f"{_SLOT_PREFIX}:{workflow_id}:{node_id}")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        return None
    try:
        return ListenSlot.from_dict(data)
    except KeyError:
        return None


def expected_event_label(object_type: str, field: str) -> str:
    """Human-readable description of what the slot is waiting for —
    surfaced in the editor's "Listening for…" chip."""
    mapping: dict[tuple[str, str], str] = {
        ("instagram", "comments"): "Instagram comment",
        ("instagram", "messaging.text"): "Instagram DM",
        ("instagram", "mentions"): "Instagram mention",
        ("instagram", "messaging.ig_story_reply"): "Instagram story reply",
        ("instagram", "messaging.ig_story_mention"): "Instagram story mention",
        ("page", "messaging.text"): "Messenger DM",
        ("page", "messaging.postback"): "Messenger button click",
        ("page", "feed.comment"): "Facebook Page comment",
        ("page", "feed.reaction"): "Facebook Page reaction",
        ("page", "mention"): "Facebook Page mention",
        ("page", "leadgen"): "Lead Ads submission",
        ("whatsapp_business_account", "wa.messages"): "WhatsApp inbound message",
        ("whatsapp_business_account", "wa.statuses"): "WhatsApp status callback",
    }
    return mapping.get((object_type, field), f"{object_type} / {field}")


__all__ = [
    "ListenSlot",
    "PollingListenSlot",
    "DEFAULT_TTL_SECONDS",
    "open_slot",
    "close_slot",
    "claim_slots_for_event",
    "list_slots_for_event",
    "claim_slot",
    "find_slot",
    "expected_event_label",
    "open_polling_slot",
    "close_polling_slot",
    "find_polling_slot",
    "is_polling_cancelled",
    "is_polling_listen_active",
    "polling_expected_event_label",
]


# ── polling-trigger listen slots ─────────────────────────────────────────

# Polling listen slots live in a separate keyspace from Meta listen
# slots because the routing model is different — webhook slots are
# indexed by `(object_type, target_id, field)` so the receiver can
# match O(1) on inbound events, whereas polling slots are claimed by
# a deadline-bounded Celery loop and just need a per-(workflow, node)
# key. Sharing one namespace would force a fake routing tuple onto
# polling slots and break the Meta atomic-claim contract.
_POLLING_SLOT_PREFIX = "polling:listen:slot"
_POLLING_CANCEL_PREFIX = "polling:listen:cancel"


@dataclass(frozen=True)
class PollingListenSlot:
    workflow_id: str
    node_id: str
    execution_id: str
    provider: str  # e.g. "gmail", "gcalendar" — picks the poller adapter
    credential_id: str
    workspace_id: str
    # ISO 8601 UTC of when the slot stops listening. Stored on the slot
    # so the Celery loop can compute its own deadline without re-reading
    # config — also surfaced to the UI for the countdown.
    deadline_iso: str

    def slot_key(self) -> str:
        return f"{_POLLING_SLOT_PREFIX}:{self.workflow_id}:{self.node_id}"

    @staticmethod
    def cancel_key(workflow_id: str, node_id: str) -> str:
        return f"{_POLLING_CANCEL_PREFIX}:{workflow_id}:{node_id}"

    def as_dict(self) -> dict[str, str]:
        return {
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "execution_id": self.execution_id,
            "provider": self.provider,
            "credential_id": self.credential_id,
            "workspace_id": self.workspace_id,
            "deadline_iso": self.deadline_iso,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PollingListenSlot:
        return cls(
            workflow_id=data["workflow_id"],
            node_id=data["node_id"],
            execution_id=data["execution_id"],
            provider=data["provider"],
            credential_id=str(data.get("credential_id") or ""),
            workspace_id=str(data.get("workspace_id") or ""),
            deadline_iso=data["deadline_iso"],
        )


async def open_polling_slot(slot: PollingListenSlot, ttl: int = DEFAULT_TTL_SECONDS) -> None:
    """Register a polling-trigger listen slot. Overwrites any prior slot
    for the same (workflow, node) and clears any leftover cancel flag —
    a fresh Listen click should always start clean."""
    redis = await get_redis()
    await redis.set(slot.slot_key(), json.dumps(slot.as_dict()), ex=ttl)
    # Clear any stale cancel flag from a previous Listen on this node so
    # the new poll loop doesn't exit immediately.
    await redis.delete(PollingListenSlot.cancel_key(slot.workflow_id, slot.node_id))


async def close_polling_slot(workflow_id: str, node_id: str) -> PollingListenSlot | None:
    """Cancel an open polling slot. Sets the cancel flag so the running
    Celery loop exits on its next tick check, deletes the slot row, and
    returns the closed slot so the caller can mark the execution
    cancelled."""
    redis = await get_redis()
    key = f"{_POLLING_SLOT_PREFIX}:{workflow_id}:{node_id}"
    raw = await redis.get(key)
    # The cancel flag is set unconditionally — even if the slot already
    # expired we want any in-flight tick to short-circuit before it
    # dispatches a now-stale execution.
    await redis.set(
        PollingListenSlot.cancel_key(workflow_id, node_id),
        "1",
        ex=DEFAULT_TTL_SECONDS,
    )
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        await redis.delete(key)
        return None
    await redis.delete(key)
    try:
        return PollingListenSlot.from_dict(data)
    except KeyError:
        return None


async def find_polling_slot(workflow_id: str, node_id: str) -> PollingListenSlot | None:
    redis = await get_redis()
    raw = await redis.get(f"{_POLLING_SLOT_PREFIX}:{workflow_id}:{node_id}")
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        return None
    try:
        return PollingListenSlot.from_dict(data)
    except KeyError:
        return None


async def is_polling_cancelled(workflow_id: str, node_id: str) -> bool:
    """The poll loop checks this before each tick so a cancel click
    short-circuits before the next provider HTTP call."""
    redis = await get_redis()
    return bool(await redis.get(PollingListenSlot.cancel_key(workflow_id, node_id)))


async def is_polling_listen_active(workflow_id: str, node_id: str) -> bool:
    """True iff a listen slot is currently open for this trigger.

    The production scheduler checks this and skips polling rows whose
    listen is active — otherwise both loops race for the same cursor
    and the scheduler can grab the event the user is testing, leaving
    the listen UI hanging."""
    redis = await get_redis()
    return bool(await redis.exists(f"{_POLLING_SLOT_PREFIX}:{workflow_id}:{node_id}"))


def polling_expected_event_label(provider: str) -> str:
    return {
        "gmail": "Gmail message",
        "gcalendar": "Calendar event",
        "gdrive": "Drive change",
        "google_sheets": "Sheet row",
        "google_tasks": "Google Task event",
        "google_forms": "Form response",
    }.get(provider, provider)

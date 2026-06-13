"""Routing tests for the Meta webhook envelope normalizer.

`_flatten_entry` and `_classify_messaging` are the dispatch layer — every
incoming Meta event flows through them on the way to the trigger map. A
silent regression here (an FB comment misclassified as a feed post, an
IG story reply masquerading as a plain DM, etc.) would either drop
events on the floor or fire the wrong workflow.
"""

from __future__ import annotations

from apps.api.app.features.meta.service import (
    _classify_messaging,
    _flatten_entry,
    _target_filters,
    _trigger_type_for,
)

# ── _flatten_entry — changes shape ────────────────────────────────────────


def test_ig_comments_flatten_one_event() -> None:
    entry = {
        "id": "17841405822304914",
        "time": 0,
        "changes": [{"field": "comments", "value": {"id": "1", "text": "hi"}}],
    }
    events = _flatten_entry("instagram", entry)
    assert events == [{"field": "comments", "value": {"id": "1", "text": "hi"}}]


def test_fb_feed_comment_is_subclassified() -> None:
    entry = {
        "id": "page123",
        "changes": [
            {
                "field": "feed",
                "value": {"item": "comment", "verb": "add", "comment_id": "c1"},
            }
        ],
    }
    events = _flatten_entry("page", entry)
    assert events[0]["field"] == "feed.comment"


def test_fb_feed_post_distinct_from_comment() -> None:
    entry = {
        "id": "page123",
        "changes": [{"field": "feed", "value": {"item": "post", "verb": "add"}}],
    }
    events = _flatten_entry("page", entry)
    assert events[0]["field"] == "feed.post"


def test_fb_feed_unknown_item_falls_through() -> None:
    entry = {
        "id": "page123",
        "changes": [{"field": "feed", "value": {"item": "share"}}],
    }
    events = _flatten_entry("page", entry)
    assert events[0]["field"] == "feed.other"


def test_change_with_no_field_is_dropped() -> None:
    entry = {"id": "x", "changes": [{"value": {"hello": "world"}}]}
    assert _flatten_entry("page", entry) == []


def test_empty_entry_returns_empty_list() -> None:
    assert _flatten_entry("page", {}) == []


# ── _classify_messaging — messaging[] sub-types ───────────────────────────


def test_messenger_text_message() -> None:
    msg = {"sender": {"id": "u"}, "message": {"text": "hi", "mid": "m1"}}
    assert _classify_messaging("page", msg) == "messaging.text"


def test_messenger_postback() -> None:
    msg = {"sender": {"id": "u"}, "postback": {"title": "Click"}}
    assert _classify_messaging("page", msg) == "messaging.postback"


def test_messenger_reaction() -> None:
    msg = {"sender": {"id": "u"}, "reaction": {"emoji": "❤"}}
    assert _classify_messaging("page", msg) == "messaging.reaction"


def test_ig_story_reply_detected_only_on_instagram_object() -> None:
    msg = {
        "sender": {"id": "u"},
        "message": {"text": "loved this", "reply_to": {"story": {"id": "s1"}}},
    }
    assert _classify_messaging("instagram", msg) == "messaging.ig_story_reply"
    # Same payload arriving under `page` must NOT be misrouted as an IG
    # story reply — Messenger doesn't have stories.
    assert _classify_messaging("page", msg) == "messaging.text"


def test_ig_story_mention_via_attachment_type() -> None:
    msg = {
        "sender": {"id": "u"},
        "message": {"attachments": [{"type": "story_mention", "payload": {"url": "x"}}]},
    }
    assert _classify_messaging("instagram", msg) == "messaging.ig_story_mention"


def test_messaging_without_message_or_action_is_unknown() -> None:
    msg = {"sender": {"id": "u"}, "timestamp": 0}
    assert _classify_messaging("page", msg) == "messaging.unknown"


# ── _trigger_type_for — routing table coverage ────────────────────────────


def test_routing_table_covers_all_phase2_events() -> None:
    cases = [
        # IG
        ("instagram", "comments", "trigger.meta.ig_comment"),
        ("instagram", "mentions", "trigger.meta.ig_mention"),
        ("instagram", "messaging.text", "trigger.meta.ig_message"),
        ("instagram", "messaging.ig_story_reply", "trigger.meta.ig_story_reply"),
        ("instagram", "messaging.ig_story_mention", "trigger.meta.ig_story_mention"),
        # Page / Messenger
        ("page", "messaging.text", "trigger.meta.fb_message"),
        ("page", "messaging.postback", "trigger.meta.fb_postback"),
        ("page", "feed.comment", "trigger.meta.fb_comment"),
        ("page", "feed.reaction", "trigger.meta.fb_reaction"),
        ("page", "mention", "trigger.meta.fb_mention"),
        # Lead Ads
        ("page", "leadgen", "trigger.meta.lead_submission"),
    ]
    for obj, field, expected in cases:
        assert _trigger_type_for(obj, field) == expected, (obj, field)


def test_unknown_combinations_return_none() -> None:
    assert _trigger_type_for("instagram", "feed.post") is None
    assert _trigger_type_for(None, "comments") is None
    assert _trigger_type_for("page", "totally-made-up") is None


# ── _target_filters — webhook router fans out by target id ────────────────


def test_target_filters_use_correct_property_per_trigger() -> None:
    assert _target_filters("trigger.meta.ig_comment", "ig1") == {"ig_account_id": "ig1"}
    assert _target_filters("trigger.meta.ig_story_reply", "ig1") == {"ig_account_id": "ig1"}
    assert _target_filters("trigger.meta.fb_message", "page1") == {"page_id": "page1"}
    assert _target_filters("trigger.meta.lead_submission", "page1") == {"page_id": "page1"}
    assert _target_filters("trigger.meta.wa_message", "waba1") == {"waba_id": "waba1"}
    assert _target_filters("trigger.meta.wa_status", "waba1") == {"waba_id": "waba1"}
    assert _target_filters("trigger.meta.unknown", "x") == {}


# ── WhatsApp envelope normalization ───────────────────────────────────────


def test_wa_inbound_message_fans_out_one_event_per_message() -> None:
    entry = {
        "id": "WABA_ID",
        "changes": [
            {
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "15551234567",
                        "phone_number_id": "PHONE_ID",
                    },
                    "contacts": [{"profile": {"name": "Alice"}, "wa_id": "15557654321"}],
                    "messages": [
                        {
                            "from": "15557654321",
                            "id": "wamid.HBgL1",
                            "timestamp": "1700000000",
                            "type": "text",
                            "text": {"body": "hi"},
                        },
                        {
                            "from": "15557654321",
                            "id": "wamid.HBgL2",
                            "timestamp": "1700000005",
                            "type": "text",
                            "text": {"body": "again"},
                        },
                    ],
                },
            }
        ],
    }
    events = _flatten_entry("whatsapp_business_account", entry)
    assert len(events) == 2
    assert all(e["field"] == "wa.messages" for e in events)
    assert events[0]["value"]["_event"]["id"] == "wamid.HBgL1"
    assert events[1]["value"]["_event"]["text"]["body"] == "again"
    # Outer metadata is preserved on every fanned-out event so the trigger
    # node doesn't have to re-thread display_phone_number / contacts.
    assert events[0]["value"]["metadata"]["phone_number_id"] == "PHONE_ID"


def test_wa_status_callback_fans_out_one_event_per_status() -> None:
    entry = {
        "id": "WABA_ID",
        "changes": [
            {
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "PHONE_ID"},
                    "statuses": [
                        {"id": "wamid.X1", "status": "sent", "timestamp": "1"},
                        {"id": "wamid.X1", "status": "delivered", "timestamp": "2"},
                        {"id": "wamid.X1", "status": "read", "timestamp": "3"},
                    ],
                },
            }
        ],
    }
    events = _flatten_entry("whatsapp_business_account", entry)
    assert len(events) == 3
    assert all(e["field"] == "wa.statuses" for e in events)
    assert [e["value"]["_event"]["status"] for e in events] == ["sent", "delivered", "read"]


def test_wa_envelope_does_not_bubble_raw_messages_field() -> None:
    """Phase 2c forks `field == messages` into `wa.messages` / `wa.statuses`.
    The raw `messages` field MUST be consumed — otherwise downstream
    `_trigger_type_for` would mis-route via the empty mapping it has for
    the raw key under whatsapp_business_account."""
    entry = {
        "id": "WABA_ID",
        "changes": [
            {
                "field": "messages",
                "value": {"messaging_product": "whatsapp", "metadata": {}},
            }
        ],
    }
    events = _flatten_entry("whatsapp_business_account", entry)
    # Both inner arrays empty → zero events, NOT one event with the raw
    # `messages` field.
    assert events == []


def test_wa_routing_table_covers_phase2c_events() -> None:
    assert (
        _trigger_type_for("whatsapp_business_account", "wa.messages") == "trigger.meta.wa_message"
    )
    assert _trigger_type_for("whatsapp_business_account", "wa.statuses") == "trigger.meta.wa_status"

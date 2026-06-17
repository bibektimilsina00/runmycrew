"""Unit tests for Google Chat action node helpers."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.gchat.gchat_node import (
    GoogleChatProperties,
    _coerce_cards,
    _normalise_message_name,
    _normalise_reaction_name,
    _to_space_name,
    format_chat_error,
)

# ── _to_space_name ─────────────────────────────────────────────────────


def test_to_space_name_wraps_bare_id():
    assert _to_space_name("AAAA") == "spaces/AAAA"


def test_to_space_name_keeps_full_path():
    assert _to_space_name("spaces/AAAA") == "spaces/AAAA"


def test_to_space_name_trims_whitespace():
    assert _to_space_name("  AAAA  ") == "spaces/AAAA"


def test_to_space_name_empty_returns_empty():
    assert _to_space_name("") == ""


# ── _normalise_message_name ────────────────────────────────────────────


def test_normalise_message_full_path_passes_through():
    full = "spaces/AAAA/messages/BBBB"
    assert _normalise_message_name(None, full) == full


def test_normalise_message_bare_id_joins_with_space():
    assert _normalise_message_name("spaces/AAAA", "BBBB") == "spaces/AAAA/messages/BBBB"


def test_normalise_message_bare_id_strips_trailing_slash():
    assert _normalise_message_name("spaces/AAAA/", "BBBB") == "spaces/AAAA/messages/BBBB"


def test_normalise_message_bare_id_without_space_raises():
    with pytest.raises(ValueError, match="full"):
        _normalise_message_name(None, "BBBB")


# ── _normalise_reaction_name ───────────────────────────────────────────


def test_normalise_reaction_requires_reactions_segment():
    with pytest.raises(ValueError, match="reactions"):
        _normalise_reaction_name("spaces/A/messages/B")


def test_normalise_reaction_keeps_full_path():
    full = "spaces/A/messages/B/reactions/C"
    assert _normalise_reaction_name(full) == full


# ── _coerce_cards ──────────────────────────────────────────────────────


def test_coerce_cards_none_returns_none():
    assert _coerce_cards(None) is None
    assert _coerce_cards("") is None
    assert _coerce_cards([]) is None


def test_coerce_cards_list_passes_through():
    cards = [{"cardId": "c1", "card": {"header": {"title": "Hi"}}}]
    assert _coerce_cards(cards) is cards


def test_coerce_cards_dict_with_card_wraps_in_list():
    card_with_id = {"cardId": "x", "card": {"header": {"title": "Y"}}}
    assert _coerce_cards(card_with_id) == [card_with_id]


def test_coerce_cards_bare_card_dict_wraps_with_generated_id():
    bare = {"header": {"title": "Hello"}}
    out = _coerce_cards(bare)
    assert out == [{"cardId": "fuse_card", "card": bare}]


def test_coerce_cards_json_string_parses():
    raw = '[{"cardId":"c1","card":{"header":{"title":"X"}}}]'
    out = _coerce_cards(raw)
    assert out == [{"cardId": "c1", "card": {"header": {"title": "X"}}}]


def test_coerce_cards_invalid_json_string_raises():
    with pytest.raises(ValueError, match="valid JSON"):
        _coerce_cards("{not valid json")


def test_coerce_cards_invalid_type_raises():
    with pytest.raises(ValueError, match="object"):
        _coerce_cards(123)


# ── GoogleChatProperties — space coercion ──────────────────────────────


def test_props_coerce_space_from_dict():
    p = GoogleChatProperties(
        operation="send_message",
        space={"id": "AAAA", "name": "spaces/AAAA", "displayName": "Engineering"},
    )
    assert p.space == "spaces/AAAA"


def test_props_coerce_space_from_bare_id():
    p = GoogleChatProperties(operation="send_message", space="AAAA")
    assert p.space == "spaces/AAAA"


def test_props_coerce_space_from_full_path():
    p = GoogleChatProperties(operation="send_message", space="spaces/AAAA")
    assert p.space == "spaces/AAAA"


def test_props_coerce_space_blank_is_none():
    p = GoogleChatProperties(operation="send_message", space="")
    assert p.space is None


def test_props_strip_message_name():
    p = GoogleChatProperties(
        operation="delete_message",
        message_name="  spaces/A/messages/B  ",
    )
    assert p.message_name == "spaces/A/messages/B"


# ── format_chat_error ──────────────────────────────────────────────────


def test_format_chat_error_product_off_400():
    body = (
        '{"error":{"code":400,"message":"Google Chat is turned off. '
        'To use Chat API, turn on Google Chat.","status":"FAILED_PRECONDITION"}}'
    )
    msg = format_chat_error(400, body)
    assert "Google Chat API error 400" in msg
    assert "Google Chat is disabled" in msg
    assert "Admin Console" in msg
    assert "Gmail" in msg


def test_format_chat_error_permission_denied_403():
    body = '{"error":{"code":403,"status":"PERMISSION_DENIED"}}'
    msg = format_chat_error(403, body)
    assert "Google Chat API error 403" in msg
    assert "Chat API isn't enabled" in msg
    assert "disconnect + reconnect" in msg


def test_format_chat_error_404_membership_hint():
    msg = format_chat_error(404, '{"error":{"code":404}}')
    assert "Google Chat API error 404" in msg
    assert "member of" in msg


def test_format_chat_error_404_app_not_configured_hint():
    body = (
        '{"error":{"code":404,"message":"Google Chat app not found. '
        "To create a Chat app, you must turn on the Chat API and "
        'configure the app in the Google Cloud console.","status":"NOT_FOUND"}}'
    )
    msg = format_chat_error(404, body)
    assert "Google Chat API error 404" in msg
    assert "Chat app configured in this GCP" in msg
    assert "Configuration" in msg
    # The membership branch must NOT fire — different fix.
    assert "member of" not in msg


def test_format_chat_error_401_token_hint():
    msg = format_chat_error(401, "")
    assert "Google Chat API error 401" in msg
    assert "Reconnect" in msg


def test_format_chat_error_429_quota_hint():
    msg = format_chat_error(429, "")
    assert "Google Chat API error 429" in msg
    assert "quota" in msg


def test_format_chat_error_unknown_status_no_hint():
    msg = format_chat_error(418, "I'm a teapot")
    assert "Google Chat API error 418" in msg
    assert "I'm a teapot" in msg
    # No specialised hint for unhandled statuses — we just surface body.
    assert "—" not in msg


def test_format_chat_error_empty_body_uses_placeholder():
    msg = format_chat_error(500, "")
    assert "(no body)" in msg


def test_format_chat_error_truncates_long_body():
    body = "x" * 1000
    msg = format_chat_error(500, body)
    # 300-char cap on snippet; status prefix + body fits well under 400.
    assert len(msg) < 400

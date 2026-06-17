"""Unit tests for Google Chat action node helpers."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.gchat.gchat_node import (
    GoogleChatProperties,
    _coerce_cards,
    _normalise_message_name,
    _normalise_reaction_name,
    _to_space_name,
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

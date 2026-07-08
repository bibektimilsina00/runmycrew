"""Unit tests for Google Contacts (People API) action node helpers."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.google.gpeople.gpeople_node import (
    GooglePeopleProperties,
    _birthday_to_struct,
    _flatten_contact,
    _normalise_addresses,
    _normalise_entries,
    _normalise_urls,
)

# ── _normalise_entries (emails / phones) ───────────────────────────────


def test_normalise_entries_wraps_bare_strings():
    assert _normalise_entries(["a@b.com", "c@d.com"]) == [
        {"value": "a@b.com"},
        {"value": "c@d.com"},
    ]


def test_normalise_entries_passes_dicts_through():
    raw = [{"value": "a@b.com", "type": "work"}, {"value": "c@d.com", "type": "home"}]
    assert _normalise_entries(raw) == raw


def test_normalise_entries_mixed_drops_invalid_dicts():
    raw = [
        "ok@example.com",
        {"value": "good@example.com"},
        {"type": "missing-value"},  # no value → dropped
        "",  # blank → dropped
    ]
    assert _normalise_entries(raw) == [
        {"value": "ok@example.com"},
        {"value": "good@example.com"},
    ]


def test_normalise_entries_non_list_returns_empty():
    assert _normalise_entries(None) == []
    assert _normalise_entries("not a list") == []
    assert _normalise_entries({}) == []


# ── _normalise_addresses ───────────────────────────────────────────────


def test_normalise_addresses_wraps_formatted_strings():
    assert _normalise_addresses(["1 Main St, Boston MA"]) == [
        {"formattedValue": "1 Main St, Boston MA"}
    ]


def test_normalise_addresses_passes_structured_dicts():
    raw = [{"streetAddress": "1 Main St", "city": "Boston", "region": "MA"}]
    assert _normalise_addresses(raw) == raw


def test_normalise_addresses_drops_empty_dicts():
    raw = [{"type": "home"}, {"streetAddress": "Real"}]
    assert _normalise_addresses(raw) == [{"streetAddress": "Real"}]


# ── _normalise_urls ────────────────────────────────────────────────────


def test_normalise_urls_wraps_strings():
    assert _normalise_urls(["https://example.com", "https://github.com/x"]) == [
        {"value": "https://example.com"},
        {"value": "https://github.com/x"},
    ]


def test_normalise_urls_drops_blanks():
    assert _normalise_urls(["", "  ", "https://ok.com"]) == [{"value": "https://ok.com"}]


# ── _birthday_to_struct ────────────────────────────────────────────────


def test_birthday_to_struct_well_formed():
    assert _birthday_to_struct("1990-05-15") == {"date": {"year": 1990, "month": 5, "day": 15}}


@pytest.mark.parametrize("bad", ["", None, "garbage", "1990-05", "1990/05/15", "abc-de-fg"])
def test_birthday_to_struct_returns_none_on_invalid(bad):
    assert _birthday_to_struct(bad) is None


# ── _flatten_contact ───────────────────────────────────────────────────


def test_flatten_contact_extracts_common_fields():
    person = {
        "resourceName": "people/c123",
        "etag": "abc==",
        "names": [{"displayName": "Alice Smith", "givenName": "Alice", "familyName": "Smith"}],
        "emailAddresses": [{"value": "alice@example.com"}, {"value": "alice@work.com"}],
        "phoneNumbers": [{"value": "+15551234567"}],
        "organizations": [{"name": "Acme", "title": "Engineer"}],
    }
    flat = _flatten_contact(person)
    assert flat["resource_name"] == "people/c123"
    assert flat["display_name"] == "Alice Smith"
    assert flat["given_name"] == "Alice"
    assert flat["family_name"] == "Smith"
    assert flat["emails"] == ["alice@example.com", "alice@work.com"]
    assert flat["phones"] == ["+15551234567"]
    assert flat["organization"] == "Acme"
    assert flat["title"] == "Engineer"
    assert flat["etag"] == "abc=="


def test_flatten_contact_handles_missing_fields():
    flat = _flatten_contact({"resourceName": "people/cX"})
    assert flat["resource_name"] == "people/cX"
    assert flat["display_name"] == ""
    assert flat["emails"] == []
    assert flat["phones"] == []
    assert flat["organization"] == ""


def test_flatten_contact_drops_emails_without_value():
    person = {
        "resourceName": "people/c1",
        "emailAddresses": [{"value": "ok@x.com"}, {"type": "no-value"}, {}],
    }
    assert _flatten_contact(person)["emails"] == ["ok@x.com"]


# ── resource_name coercion ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"resourceName": "people/c1", "name": "Alice"}, "people/c1"),
        ({"id": "people/c2", "title": "Bob"}, "people/c2"),
        ("people/c3", "people/c3"),
        (None, None),
        ("", None),
        ({}, None),
        ({"resourceName": ""}, None),
    ],
)
def test_resource_name_coercion(raw, expected):
    props = GooglePeopleProperties(resource_name=raw)
    assert props.resource_name == expected

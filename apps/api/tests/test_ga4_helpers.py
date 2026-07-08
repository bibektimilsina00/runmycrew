"""Unit tests for Google Analytics 4 action node helpers."""

from __future__ import annotations

import json

import pytest

from apps.api.app.node_system.base.errors import STRUCTURED_ERROR_SENTINEL
from apps.api.app.node_system.nodes.google.ga4.ga4_node import (
    GoogleAnalyticsProperties,
    _coerce_json_field,
    _normalise_date,
    _parse_name_list,
    _to_account_name,
    _to_property_name,
    format_ga4_error,
)


def _decode_structured(error_string: str) -> dict:
    assert error_string.startswith(STRUCTURED_ERROR_SENTINEL), error_string
    return json.loads(error_string[len(STRUCTURED_ERROR_SENTINEL) :])


# ── _to_property_name / _to_account_name ───────────────────────────────


def test_to_property_name_wraps_bare_id():
    assert _to_property_name("123456789") == "properties/123456789"


def test_to_property_name_keeps_full_path():
    assert _to_property_name("properties/123456789") == "properties/123456789"


def test_to_property_name_empty_returns_empty():
    assert _to_property_name("") == ""


def test_to_account_name_wraps_bare_id():
    assert _to_account_name("987") == "accounts/987"


def test_to_account_name_keeps_full_path():
    assert _to_account_name("accounts/987") == "accounts/987"


# ── _normalise_date ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value, expected",
    [
        ("today", "today"),
        ("yesterday", "yesterday"),
        ("30daysAgo", "30daysAgo"),
        ("2024-01-01", "2024-01-01"),
        ("  today  ", "today"),
    ],
)
def test_normalise_date_passes_valid_shapes(value, expected):
    assert _normalise_date(value) == expected


def test_normalise_date_forwards_unknown_shape():
    # Forward as-is so the API gives a clear 400 — we don't second-guess.
    assert _normalise_date("garbage") == "garbage"


# ── _parse_name_list ───────────────────────────────────────────────────


def test_parse_name_list_comma_separated_string():
    assert _parse_name_list("country, deviceCategory ,city") == [
        "country",
        "deviceCategory",
        "city",
    ]


def test_parse_name_list_json_array_string():
    assert _parse_name_list('["country","city"]') == ["country", "city"]


def test_parse_name_list_python_list():
    assert _parse_name_list(["country", "city"]) == ["country", "city"]


def test_parse_name_list_empty_returns_empty():
    assert _parse_name_list("") == []
    assert _parse_name_list(None) == []
    assert _parse_name_list([]) == []


def test_parse_name_list_filters_empty_segments():
    assert _parse_name_list("country, , city") == ["country", "city"]


def test_parse_name_list_invalid_type_raises():
    with pytest.raises(ValueError, match="comma-separated"):
        _parse_name_list(123)


# ── _coerce_json_field ─────────────────────────────────────────────────


def test_coerce_json_field_empty_returns_none():
    assert _coerce_json_field(None) is None
    assert _coerce_json_field("") is None
    assert _coerce_json_field({}) is None
    assert _coerce_json_field([]) is None


def test_coerce_json_field_dict_passes_through():
    raw = {"filter": {"fieldName": "country"}}
    assert _coerce_json_field(raw) is raw


def test_coerce_json_field_list_passes_through():
    raw = [{"metric": {"metricName": "sessions"}, "desc": True}]
    assert _coerce_json_field(raw) is raw


def test_coerce_json_field_json_string_parses():
    raw = '{"filter":{"fieldName":"country"}}'
    assert _coerce_json_field(raw) == {"filter": {"fieldName": "country"}}


def test_coerce_json_field_invalid_json_raises():
    with pytest.raises(ValueError, match="valid JSON"):
        _coerce_json_field("{not valid")


# ── GoogleAnalyticsProperties — property / account coercion ────────────


def test_props_coerce_property_from_dict():
    p = GoogleAnalyticsProperties(
        operation="run_report",
        property={"id": "123", "name": "properties/123", "displayName": "Site"},
    )
    assert p.property == "properties/123"


def test_props_coerce_property_from_bare_id():
    p = GoogleAnalyticsProperties(operation="run_report", property="123")
    assert p.property == "properties/123"


def test_props_coerce_property_from_full_path():
    p = GoogleAnalyticsProperties(operation="run_report", property="properties/123")
    assert p.property == "properties/123"


def test_props_coerce_property_blank_is_none():
    p = GoogleAnalyticsProperties(operation="run_report", property="")
    assert p.property is None


def test_props_coerce_account_from_dict():
    p = GoogleAnalyticsProperties(operation="list_properties", account={"id": "999"})
    assert p.account == "accounts/999"


def test_props_coerce_account_from_bare_id():
    p = GoogleAnalyticsProperties(operation="list_properties", account="999")
    assert p.account == "accounts/999"


# ── format_ga4_error structured paths ──────────────────────────────────


def test_format_ga4_error_permission_denied_403_structured():
    body = '{"error":{"code":403,"message":"User does not have sufficient permissions"}}'
    payload = _decode_structured(format_ga4_error(403, body))
    assert "rejected" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "property access management" in actions
    assert "analyticsdata.googleapis.com" in actions


def test_format_ga4_error_404_structured():
    payload = _decode_structured(format_ga4_error(404, '{"error":{"code":404}}'))
    assert "not found" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "property picker" in actions


def test_format_ga4_error_400_structured():
    payload = _decode_structured(format_ga4_error(400, "INVALID_ARGUMENT"))
    assert "invalid" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "get_metadata" in actions
    assert "check_compatibility" in actions


def test_format_ga4_error_429_structured():
    payload = _decode_structured(format_ga4_error(429, ""))
    assert "quota" in payload["title"].lower()


def test_format_ga4_error_unknown_status_falls_through():
    msg = format_ga4_error(418, "teapot")
    assert not msg.startswith(STRUCTURED_ERROR_SENTINEL)
    assert "GA4 API error 418" in msg
    assert "teapot" in msg

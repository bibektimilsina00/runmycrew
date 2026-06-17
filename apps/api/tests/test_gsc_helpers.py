"""Unit tests for Google Search Console action node helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from apps.api.app.node_system.base.errors import STRUCTURED_ERROR_SENTINEL
from apps.api.app.node_system.nodes.gsc.gsc_node import (
    GoogleSearchConsoleProperties,
    _coerce_json_field,
    _normalise_date,
    _parse_name_list,
    _site_path,
    _to_site_url,
    format_gsc_error,
)


def _decode_structured(error_string: str) -> dict:
    assert error_string.startswith(STRUCTURED_ERROR_SENTINEL), error_string
    return json.loads(error_string[len(STRUCTURED_ERROR_SENTINEL) :])


# ── _to_site_url ───────────────────────────────────────────────────────


def test_to_site_url_keeps_domain_property():
    assert _to_site_url("sc-domain:example.com") == "sc-domain:example.com"


def test_to_site_url_keeps_url_prefix_with_slash():
    assert _to_site_url("https://example.com/") == "https://example.com/"


def test_to_site_url_adds_trailing_slash_to_url_prefix():
    assert _to_site_url("https://example.com") == "https://example.com/"


def test_to_site_url_promotes_bare_host_to_https():
    assert _to_site_url("example.com") == "https://example.com/"


def test_to_site_url_keeps_http_scheme():
    assert _to_site_url("http://example.com") == "http://example.com/"


def test_to_site_url_empty_returns_empty():
    assert _to_site_url("") == ""


# ── _site_path (URL encoding) ──────────────────────────────────────────


def test_site_path_encodes_url_prefix():
    # `https://` must become `https%3A%2F%2F` for the API.
    encoded = _site_path("https://example.com/")
    assert "%3A" in encoded
    assert "%2F" in encoded


def test_site_path_encodes_domain_property_colon():
    # `sc-domain:` must encode to `sc-domain%3A`.
    encoded = _site_path("sc-domain:example.com")
    assert encoded.startswith("sc-domain%3A")


# ── _normalise_date ────────────────────────────────────────────────────


def test_normalise_date_absolute_passes_through():
    assert _normalise_date("2024-01-15") == "2024-01-15"


def test_normalise_date_today_resolves_to_iso():
    today = datetime.now(UTC).date()
    assert _normalise_date("today") == today.isoformat()


def test_normalise_date_yesterday_resolves_to_iso():
    today = datetime.now(UTC).date()
    expected = (today - timedelta(days=1)).isoformat()
    assert _normalise_date("yesterday") == expected


def test_normalise_date_ndaysago_resolves_to_iso():
    today = datetime.now(UTC).date()
    expected = (today - timedelta(days=7)).isoformat()
    assert _normalise_date("7daysAgo") == expected
    # Case-insensitive.
    assert _normalise_date("7daysago") == expected


def test_normalise_date_unknown_shape_forwards_verbatim():
    # Let the API return a clear 400 rather than guessing.
    assert _normalise_date("nextWeek") == "nextWeek"


def test_normalise_date_empty_returns_empty():
    assert _normalise_date("") == ""


# ── _parse_name_list ───────────────────────────────────────────────────


def test_parse_name_list_comma_separated():
    assert _parse_name_list("query, page, country") == ["query", "page", "country"]


def test_parse_name_list_json_array_string():
    assert _parse_name_list('["query","device"]') == ["query", "device"]


def test_parse_name_list_python_list():
    assert _parse_name_list(["query", "device"]) == ["query", "device"]


def test_parse_name_list_empty():
    assert _parse_name_list("") == []
    assert _parse_name_list(None) == []


# ── _coerce_json_field ─────────────────────────────────────────────────


def test_coerce_json_field_dict_passes_through():
    raw = {"groupType": "and", "filters": []}
    assert _coerce_json_field(raw) is raw


def test_coerce_json_field_json_string_parses():
    raw = '{"groupType":"and","filters":[]}'
    assert _coerce_json_field(raw) == {"groupType": "and", "filters": []}


def test_coerce_json_field_empty_returns_none():
    assert _coerce_json_field(None) is None
    assert _coerce_json_field("") is None
    assert _coerce_json_field([]) is None
    assert _coerce_json_field({}) is None


def test_coerce_json_field_invalid_json_raises():
    with pytest.raises(ValueError, match="valid JSON"):
        _coerce_json_field("{not valid")


# ── GoogleSearchConsoleProperties — site coercion ──────────────────────


def test_props_coerce_site_from_dict():
    p = GoogleSearchConsoleProperties(
        operation="query_search_analytics",
        site={"siteUrl": "https://example.com/", "permissionLevel": "siteOwner"},
    )
    assert p.site == "https://example.com/"


def test_props_coerce_site_from_bare_url():
    p = GoogleSearchConsoleProperties(
        operation="query_search_analytics",
        site="https://example.com",
    )
    # _to_site_url adds the trailing slash.
    assert p.site == "https://example.com/"


def test_props_coerce_site_from_domain_property():
    p = GoogleSearchConsoleProperties(
        operation="query_search_analytics",
        site="sc-domain:example.com",
    )
    assert p.site == "sc-domain:example.com"


def test_props_coerce_site_blank_is_none():
    p = GoogleSearchConsoleProperties(operation="query_search_analytics", site="")
    assert p.site is None


# ── format_gsc_error ──────────────────────────────────────────────────


def test_format_gsc_error_permission_denied_403_structured():
    body = '{"error":{"code":403,"message":"User does not have sufficient permissions"}}'
    payload = _decode_structured(format_gsc_error(403, body))
    assert "rejected" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "users and permissions" in actions
    assert "searchconsole.googleapis.com" in actions


def test_format_gsc_error_404_structured():
    payload = _decode_structured(format_gsc_error(404, '{"error":{"code":404}}'))
    assert "not found" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "site picker" in actions
    assert "sc-domain" in actions


def test_format_gsc_error_400_structured():
    payload = _decode_structured(format_gsc_error(400, "INVALID_ARGUMENT"))
    assert "invalid" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "query_search_analytics" in actions
    assert "searchappearance" in actions


def test_format_gsc_error_429_structured():
    payload = _decode_structured(format_gsc_error(429, ""))
    assert "quota" in payload["title"].lower()


def test_format_gsc_error_unknown_status_falls_through():
    msg = format_gsc_error(418, "teapot")
    assert not msg.startswith(STRUCTURED_ERROR_SENTINEL)
    assert "Search Console API error 418" in msg
    assert "teapot" in msg

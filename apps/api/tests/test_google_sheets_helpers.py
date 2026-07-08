"""Unit tests for the Sheets action node helpers.

Pure-function tests for the bits that get reused across multiple ops —
column-letter math, dict→row mapping, A1 → grid-range parsing, hex
colour conversion.
"""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.google.google_sheets.google_sheets import (
    _column_letter,
    _hex_to_rgb01,
    _parse_range_for_grid,
    _row_dict_to_values,
)


@pytest.mark.parametrize(
    ("idx", "expected"),
    [
        (0, "A"),
        (1, "B"),
        (25, "Z"),
        (26, "AA"),
        (27, "AB"),
        (51, "AZ"),
        (52, "BA"),
        (701, "ZZ"),
        (702, "AAA"),
    ],
)
def test_column_letter(idx, expected):
    assert _column_letter(idx) == expected


def test_row_dict_maps_headers_in_order():
    headers = ["Name", "Email", "Age"]
    assert _row_dict_to_values(
        {"Name": "Alice", "Email": "a@b.com", "Age": 30},
        headers,
    ) == ["Alice", "a@b.com", 30]


def test_row_dict_inserts_blanks_for_missing_keys():
    headers = ["Name", "Email", "Age"]
    assert _row_dict_to_values({"Name": "Alice"}, headers) == [
        "Alice",
        "",
        "",
    ]


def test_row_dict_silently_drops_unknown_keys():
    """Mapping a typo to an arbitrary column would corrupt data — keep
    the strict-by-headers contract."""
    headers = ["Name", "Email"]
    assert _row_dict_to_values({"Name": "Alice", "Phone": "555"}, headers) == ["Alice", ""]


def test_parse_range_simple():
    assert _parse_range_for_grid("Sheet1!A1:D10") == {
        "sheet_name": "Sheet1",
        "startColumnIndex": 0,
        "endColumnIndex": 4,
        "startRowIndex": 0,
        "endRowIndex": 10,
    }


def test_parse_range_column_only():
    assert _parse_range_for_grid("Sheet1!A:C") == {
        "sheet_name": "Sheet1",
        "startColumnIndex": 0,
        "endColumnIndex": 3,
    }


def test_parse_range_handles_multi_letter_columns():
    parsed = _parse_range_for_grid("Sheet1!AA1:AB2")
    assert parsed == {
        "sheet_name": "Sheet1",
        "startColumnIndex": 26,
        "endColumnIndex": 28,
        "startRowIndex": 0,
        "endRowIndex": 2,
    }


def test_parse_range_strips_quoted_sheet_name():
    parsed = _parse_range_for_grid("'My Sheet'!A1:B2")
    assert parsed is not None
    assert parsed["sheet_name"] == "My Sheet"


def test_parse_range_returns_none_on_garbage():
    assert _parse_range_for_grid("not a range") is None
    assert _parse_range_for_grid("Sheet1!nope") is None
    assert _parse_range_for_grid("") is None


def test_hex_to_rgb01_well_formed():
    assert _hex_to_rgb01("#ffffff") == {"red": 1.0, "green": 1.0, "blue": 1.0}
    assert _hex_to_rgb01("#000000") == {"red": 0.0, "green": 0.0, "blue": 0.0}


def test_hex_to_rgb01_accepts_missing_hash():
    assert _hex_to_rgb01("ff0000") == {"red": 1.0, "green": 0.0, "blue": 0.0}


@pytest.mark.parametrize("bad", ["", "abc", "#nothex", "#abc", "#abcdefg"])
def test_hex_to_rgb01_rejects_garbage(bad):
    assert _hex_to_rgb01(bad) is None

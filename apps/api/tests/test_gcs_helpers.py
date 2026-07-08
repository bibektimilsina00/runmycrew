"""Unit tests for Google Cloud Storage action node helpers."""

from __future__ import annotations

import json

import pytest

from apps.api.app.node_system.base.errors import STRUCTURED_ERROR_SENTINEL
from apps.api.app.node_system.nodes.google.gcs.gcs_node import (
    GoogleCloudStorageProperties,
    _coerce_json_field,
    _object_path,
    format_gcs_error,
)


def _decode_structured(error_string: str) -> dict:
    assert error_string.startswith(STRUCTURED_ERROR_SENTINEL), error_string
    return json.loads(error_string[len(STRUCTURED_ERROR_SENTINEL) :])


# ── _object_path (URL encoding) ────────────────────────────────────────


def test_object_path_encodes_slash():
    # Object names can contain `/` which must encode to `%2F` so the
    # API doesn't treat it as a path separator.
    assert _object_path("dir/sub/file.txt") == "dir%2Fsub%2Ffile.txt"


def test_object_path_encodes_spaces_and_unicode():
    assert _object_path("my file.txt") == "my%20file.txt"
    assert _object_path("日本/file") == "%E6%97%A5%E6%9C%AC%2Ffile"


def test_object_path_keeps_alphanumerics():
    assert _object_path("simple.txt") == "simple.txt"


# ── _coerce_json_field ─────────────────────────────────────────────────


def test_coerce_json_field_dict_passes_through():
    raw = {"meta": "value"}
    assert _coerce_json_field(raw) is raw


def test_coerce_json_field_json_string_parses():
    raw = '{"meta":"value"}'
    assert _coerce_json_field(raw) == {"meta": "value"}


def test_coerce_json_field_empty_returns_none():
    assert _coerce_json_field(None) is None
    assert _coerce_json_field("") is None
    assert _coerce_json_field({}) is None
    assert _coerce_json_field([]) is None


def test_coerce_json_field_invalid_json_raises():
    with pytest.raises(ValueError, match="valid JSON"):
        _coerce_json_field("{not valid")


# ── GoogleCloudStorageProperties — coercion ────────────────────────────


def test_props_bucket_from_dict():
    p = GoogleCloudStorageProperties(
        operation="get_bucket",
        bucket={"name": "my-bucket", "location": "us"},
    )
    assert p.bucket == "my-bucket"


def test_props_bucket_strips_whitespace():
    p = GoogleCloudStorageProperties(operation="get_bucket", bucket="  my-bucket  ")
    assert p.bucket == "my-bucket"


def test_props_bucket_blank_is_none():
    p = GoogleCloudStorageProperties(operation="get_bucket", bucket="")
    assert p.bucket is None


def test_props_destination_bucket_from_dict():
    p = GoogleCloudStorageProperties(
        operation="copy_object",
        destination_bucket={"name": "dst-bucket"},
    )
    assert p.destination_bucket == "dst-bucket"


def test_props_object_name_strips_whitespace():
    p = GoogleCloudStorageProperties(operation="delete_object", object_name="  path/to/file  ")
    assert p.object_name == "path/to/file"


def test_props_project_id_blank_is_none():
    p = GoogleCloudStorageProperties(operation="list_buckets", project_id="")
    assert p.project_id is None


# ── format_gcs_error ──────────────────────────────────────────────────


def test_format_gcs_error_permission_denied_403():
    body = (
        '{"error":{"code":403,"message":"user@example.com does not '
        'have storage.buckets.list access"}}'
    )
    payload = _decode_structured(format_gcs_error(403, body))
    assert "rejected" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "storage object admin" in actions
    assert "storage.googleapis.com" in actions


def test_format_gcs_error_404():
    payload = _decode_structured(format_gcs_error(404, '{"error":{"code":404}}'))
    assert "not found" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "case-sensitive" in actions


def test_format_gcs_error_409_conflict():
    payload = _decode_structured(format_gcs_error(409, "CONFLICT"))
    assert "conflict" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "globally unique" in actions
    assert "delete_bucket" in actions


def test_format_gcs_error_400():
    payload = _decode_structured(format_gcs_error(400, "INVALID_ARGUMENT"))
    assert "invalid" in payload["title"].lower()
    actions = " ".join(payload["actions"]).lower()
    assert "3-63" in actions
    assert "storage classes" in actions


def test_format_gcs_error_429():
    payload = _decode_structured(format_gcs_error(429, ""))
    assert "quota" in payload["title"].lower() or "rate" in payload["title"].lower()


def test_format_gcs_error_unknown_status_falls_through():
    msg = format_gcs_error(418, "teapot")
    assert not msg.startswith(STRUCTURED_ERROR_SENTINEL)
    assert "Cloud Storage API error 418" in msg
    assert "teapot" in msg

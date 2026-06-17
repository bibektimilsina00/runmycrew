"""Google Cloud Storage action node — one node, 10 operations.

Buckets:
  - ``list_buckets``   — buckets under a GCP project
  - ``get_bucket``     — bucket metadata
  - ``create_bucket``  — create in a project + location + storage class
  - ``delete_bucket``  — must be empty

Objects:
  - ``list_objects``       — paged, with prefix + delimiter
  - ``get_object_metadata`` — JSON metadata (size, contentType, md5, …)
  - ``download_object``    — body content (text by default, base64 for
    binary)
  - ``upload_object``      — from URL / Library asset / inline content
  - ``delete_object``
  - ``copy_object``        — src → dst (cross-bucket allowed)

OAuth scope: ``devstorage.read_write`` (added to GoogleOAuthProvider).
Covers list / read / write / delete for objects + bucket CRUD. Doesn't
include ACL management — out of scope for v1; that needs the broader
``devstorage.full_control``.

Notes from build
  - GCS object names can contain ``/``. The API treats them as opaque
    strings, so we URL-encode them with ``safe=""`` at every endpoint.
  - Bucket names are globally unique; no project namespace inside the
    path.
  - Upload uses the ``uploadType=media`` simple-upload path with a
    separate ``contentType`` query param. Metadata uploads (with a
    custom MIME, cache-control, …) use the same multipart wrapper
    pattern Drive uses — single POST, JSON metadata part + binary data
    part.
  - Downloads default to a UTF-8 decode for text content (so workflows
    can pipe straight into LLMs / Sheets). Set ``download_as_binary``
    to return base64 + the original byte length.
"""

from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.errors import make_structured_error
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

STORAGE_API = "https://storage.googleapis.com/storage/v1"
UPLOAD_API = "https://storage.googleapis.com/upload/storage/v1"


def format_gcs_error(status_code: int, body: str) -> str:
    """Turn a Cloud Storage error into a structured error payload."""
    snippet = (body or "").strip()[:600]
    lower = snippet.lower()

    if status_code == 403 and "does not have storage" in lower:
        return make_structured_error(
            "Cloud Storage rejected the request",
            summary=(
                "The connected Google account doesn't have the IAM "
                "role needed for this operation on this bucket, or "
                "the Cloud Storage API isn't enabled for the GCP "
                "project."
            ),
            actions=[
                "GCP Console → Cloud Storage → bucket → Permissions → grant the connected account `Storage Object Admin` (or narrower role) on the bucket.",
                "GCP Console → APIs & Services → Library → enable `storage.googleapis.com`.",
                "Disconnect + reconnect the Google credential to grant the `devstorage.read_write` scope if you connected before today.",
            ],
            raw=snippet,
        )

    if status_code == 404:
        return make_structured_error(
            "Cloud Storage resource not found",
            summary=(
                "The bucket or object name doesn't exist, or the connected account can't see it."
            ),
            actions=[
                "Re-open the bucket picker and re-select.",
                "Object names are case-sensitive and include any folder path (e.g. `dir/file.txt`).",
            ],
            raw=snippet,
        )

    if status_code == 409:
        return make_structured_error(
            "Cloud Storage conflict",
            summary=(
                "The target name is already taken, or the bucket "
                "isn't empty (`delete_bucket` requires an empty "
                "bucket)."
            ),
            actions=[
                "Bucket names are GLOBALLY unique across all GCP users — pick a different name.",
                "For delete_bucket: list_objects + delete each before retrying.",
            ],
            raw=snippet,
        )

    if status_code == 400:
        return make_structured_error(
            "Cloud Storage request invalid",
            summary=(
                "The API rejected the request body — most often a "
                "bad bucket name, an unsupported storage class, or "
                "an invalid location code."
            ),
            actions=[
                "Bucket names: 3-63 chars, lowercase, no underscores. Must start with a letter or number.",
                "Storage classes: STANDARD, NEAREST, NEARLINE, COLDLINE, ARCHIVE.",
                "Locations: `us`, `eu`, `asia` for multi-region; `us-central1`, `europe-west1`, etc for single-region.",
            ],
            raw=snippet,
        )

    if status_code == 429:
        return make_structured_error(
            "Cloud Storage quota / rate limit hit",
            summary=(
                "The project hit a Cloud Storage rate limit. Most limits refill within a second."
            ),
            actions=[
                "Retry with backoff.",
                "GCP Console → IAM & Admin → Quotas if you need a higher cap.",
            ],
            raw=snippet,
        )

    return f"Cloud Storage API error {status_code}: {snippet or '(no body)'}"


def _object_path(name: str) -> str:
    """URL-encode an object name for use as a path segment. Objects
    can contain ``/`` which must encode to ``%2F`` — the API treats the
    name as opaque."""
    return quote(name, safe="")


def _coerce_json_field(raw: Any) -> Any:
    if raw in (None, "", [], {}):
        return None
    if isinstance(raw, dict | list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Field must be valid JSON: {exc.msg}") from exc
    raise ValueError(f"Expected object / array / JSON string, got {type(raw).__name__}.")


_STORAGE_CLASS_OPTIONS: list[dict[str, str]] = [
    {"label": "Standard (default)", "value": ""},
    {"label": "Standard", "value": "STANDARD"},
    {"label": "Nearline", "value": "NEARLINE"},
    {"label": "Coldline", "value": "COLDLINE"},
    {"label": "Archive", "value": "ARCHIVE"},
]


class GoogleCloudStorageProperties(BaseModel):
    credential: str | None = None
    operation: str = "list_objects"

    project_id: str | None = None
    bucket: str | None = None
    object_name: str | None = None

    # create_bucket
    location: str | None = None
    storage_class: str | None = None

    # list_objects
    prefix: str | None = None
    delimiter: str | None = None
    page_size: int | None = None
    page_token: str | None = None

    # download_object
    download_as_binary: bool = False

    # upload_object
    content: Any = None  # Media field — URL / asset / inline
    content_type: str | None = None
    cache_control: str | None = None
    metadata: Any = None  # custom user metadata dict

    # copy_object
    destination_bucket: str | None = None
    destination_object: str | None = None

    @field_validator("bucket", "destination_bucket", mode="before")
    @classmethod
    def _coerce_bucket(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        if isinstance(value, dict):
            v = value.get("name") or value.get("id") or ""
            return str(v).strip() or None
        return str(value).strip() or None

    @field_validator(
        "object_name",
        "destination_object",
        "project_id",
        "location",
        mode="before",
    )
    @classmethod
    def _strip_str(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value).strip() or None


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GoogleCloudStorageNode(BaseNode[GoogleCloudStorageProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleCloudStorageProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gcs",
            name="Google Cloud Storage",
            category="integration",
            description=(
                "Manage Cloud Storage buckets and objects — list, "
                "read, write, copy, delete. Object uploads can pull "
                "from a URL, a Fuse Library asset, or inline content."
            ),
            icon="si:SiGooglecloudstorage",
            color="#4285f4",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "list_objects",
                    "options": [
                        {"label": "List buckets", "value": "list_buckets"},
                        {"label": "Get bucket", "value": "get_bucket"},
                        {"label": "Create bucket", "value": "create_bucket"},
                        {"label": "Delete bucket", "value": "delete_bucket"},
                        {"label": "List objects", "value": "list_objects"},
                        {"label": "Get object metadata", "value": "get_object_metadata"},
                        {"label": "Download object", "value": "download_object"},
                        {"label": "Upload object", "value": "upload_object"},
                        {"label": "Delete object", "value": "delete_object"},
                        {"label": "Copy object", "value": "copy_object"},
                    ],
                },
                {
                    "name": "project_id",
                    "label": "Project ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "my-gcp-project-id",
                    "description": (
                        "GCP project. Find it in Cloud Console → "
                        "project picker (top bar). Needed for "
                        "bucket-list and bucket-create only."
                    ),
                    "condition": _cond_any("list_buckets", "create_bucket"),
                },
                {
                    "name": "bucket",
                    "label": "Bucket",
                    "type": "gcs-bucket",
                    "required": True,
                    "condition": _cond_any(
                        "get_bucket",
                        "delete_bucket",
                        "list_objects",
                        "get_object_metadata",
                        "download_object",
                        "upload_object",
                        "delete_object",
                        "copy_object",
                    ),
                },
                # Bucket project_id when using a bucket picker — picker
                # needs it to filter.
                {
                    "name": "project_id",
                    "label": "Project ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "my-gcp-project-id",
                    "description": "Project the bucket lives in — required to populate the picker.",
                    "condition": _cond_any(
                        "get_bucket",
                        "delete_bucket",
                        "list_objects",
                        "get_object_metadata",
                        "download_object",
                        "upload_object",
                        "delete_object",
                        "copy_object",
                    ),
                },
                # create_bucket
                {
                    "name": "bucket",
                    "label": "New bucket name",
                    "type": "string",
                    "required": True,
                    "placeholder": "my-unique-bucket-name",
                    "description": (
                        "3-63 lowercase letters / digits / hyphens / dots. "
                        "Globally unique across all GCP users."
                    ),
                    "condition": _cond("create_bucket"),
                },
                {
                    "name": "location",
                    "label": "Location",
                    "type": "string",
                    "default": "us-central1",
                    "placeholder": "us-central1",
                    "description": "Single-region (`us-central1`) or multi-region (`us`, `eu`, `asia`).",
                    "condition": _cond("create_bucket"),
                },
                {
                    "name": "storage_class",
                    "label": "Storage class",
                    "type": "options",
                    "default": "",
                    "options": _STORAGE_CLASS_OPTIONS,
                    "condition": _cond("create_bucket"),
                    "mode": "advanced",
                },
                # object_name
                {
                    "name": "object_name",
                    "label": "Object name",
                    "type": "string",
                    "required": True,
                    "placeholder": "path/to/file.txt",
                    "description": "Full object path. May contain `/` — treated as part of the name, not a folder hierarchy.",
                    "condition": _cond_any(
                        "get_object_metadata",
                        "download_object",
                        "upload_object",
                        "delete_object",
                        "copy_object",
                    ),
                },
                # list_objects filters
                {
                    "name": "prefix",
                    "label": "Prefix",
                    "type": "string",
                    "placeholder": "uploads/",
                    "description": "Filter to objects whose name starts with this prefix.",
                    "condition": _cond("list_objects"),
                },
                {
                    "name": "delimiter",
                    "label": "Delimiter",
                    "type": "string",
                    "placeholder": "/",
                    "description": "Group results by delimiter — e.g. `/` lists virtual folders under the prefix.",
                    "condition": _cond("list_objects"),
                    "mode": "advanced",
                },
                {
                    "name": "page_size",
                    "label": "Page size",
                    "type": "number",
                    "default": 100,
                    "condition": _cond("list_objects"),
                    "mode": "advanced",
                },
                {
                    "name": "page_token",
                    "label": "Page token",
                    "type": "string",
                    "placeholder": "{{ $node('Google Cloud Storage').nextPageToken }}",
                    "condition": _cond("list_objects"),
                    "mode": "advanced",
                },
                # download
                {
                    "name": "download_as_binary",
                    "label": "Return as binary (base64)",
                    "type": "boolean",
                    "default": False,
                    "description": "On: emit `{content_base64, content_length, content_type}` so binary survives JSON. Off: best-effort UTF-8 decode + raw `text` field.",
                    "condition": _cond("download_object"),
                    "mode": "advanced",
                },
                # upload inputs
                {
                    "name": "content",
                    "label": "Content",
                    "type": "media",
                    "required": True,
                    "description": "From a URL, a Fuse Library asset, or paste inline content.",
                    "condition": _cond("upload_object"),
                },
                {
                    "name": "content_type",
                    "label": "Content type (MIME)",
                    "type": "string",
                    "placeholder": "text/plain",
                    "description": "Override MIME. Defaults to whatever the source returns, falling back to `application/octet-stream`.",
                    "condition": _cond("upload_object"),
                    "mode": "advanced",
                },
                {
                    "name": "cache_control",
                    "label": "Cache-Control header",
                    "type": "string",
                    "placeholder": "public, max-age=3600",
                    "condition": _cond("upload_object"),
                    "mode": "advanced",
                },
                {
                    "name": "metadata",
                    "label": "Custom metadata (JSON)",
                    "type": "json",
                    "placeholder": '{ "uploaded-by": "fuse" }',
                    "description": "Forwarded as `metadata.{}` on the object — read back via `get_object_metadata`.",
                    "condition": _cond("upload_object"),
                    "mode": "advanced",
                },
                # copy
                {
                    "name": "destination_bucket",
                    "label": "Destination bucket",
                    "type": "gcs-bucket",
                    "required": True,
                    "condition": _cond("copy_object"),
                },
                {
                    "name": "destination_object",
                    "label": "Destination object name",
                    "type": "string",
                    "required": True,
                    "placeholder": "destination/path.txt",
                    "condition": _cond("copy_object"),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "name", "type": "string"},
                {"label": "bucket", "type": "string"},
                {"label": "size", "type": "string"},
                {"label": "contentType", "type": "string"},
                {"label": "items", "type": "array"},
                {"label": "prefixes", "type": "array"},
                {"label": "nextPageToken", "type": "string"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=format_gcs_error(exc.response.status_code, exc.response.text),
            )
        except ValueError as exc:
            return NodeResult(success=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleCloudStorageNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── shared helpers ──────────────────────────────────────────────────────


def _require_bucket(node: GoogleCloudStorageNode) -> str | NodeResult:
    b = (node.props.bucket or "").strip()
    if not b:
        return NodeResult(success=False, error="Bucket is required.")
    return b


def _require_object(node: GoogleCloudStorageNode) -> str | NodeResult:
    obj = (node.props.object_name or "").strip()
    if not obj:
        return NodeResult(success=False, error="Object name is required.")
    return obj


def _require_project(node: GoogleCloudStorageNode) -> str | NodeResult:
    p = (node.props.project_id or "").strip()
    if not p:
        return NodeResult(success=False, error="Project ID is required.")
    return p


# ── handlers ────────────────────────────────────────────────────────────


async def _list_buckets(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    project = _require_project(node)
    if isinstance(project, NodeResult):
        return project
    params: dict[str, Any] = {"project": project}
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(f"{STORAGE_API}/b", headers=headers, params=params)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_bucket(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    r = await client.get(f"{STORAGE_API}/b/{quote(bucket, safe='')}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _create_bucket(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    project = _require_project(node)
    if isinstance(project, NodeResult):
        return project
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    body: dict[str, Any] = {"name": bucket}
    if node.props.location:
        body["location"] = node.props.location.strip().lower()
    sc = (node.props.storage_class or "").strip().upper()
    if sc:
        body["storageClass"] = sc
    r = await client.post(
        f"{STORAGE_API}/b",
        headers=headers,
        params={"project": project},
        json=body,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _delete_bucket(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    r = await client.delete(f"{STORAGE_API}/b/{quote(bucket, safe='')}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data={"bucket": bucket, "deleted": True})


async def _list_objects(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    params: dict[str, Any] = {}
    if node.props.prefix:
        params["prefix"] = node.props.prefix
    if node.props.delimiter:
        params["delimiter"] = node.props.delimiter
    if node.props.page_size:
        params["maxResults"] = max(1, min(int(node.props.page_size), 1000))
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    r = await client.get(
        f"{STORAGE_API}/b/{quote(bucket, safe='')}/o",
        headers=headers,
        params=params,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_object_metadata(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    obj = _require_object(node)
    if isinstance(obj, NodeResult):
        return obj
    r = await client.get(
        f"{STORAGE_API}/b/{quote(bucket, safe='')}/o/{_object_path(obj)}",
        headers=headers,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _download_object(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    obj = _require_object(node)
    if isinstance(obj, NodeResult):
        return obj
    # Strip the JSON Content-Type header — the media-download response
    # is the raw object body, not JSON.
    media_headers = {"Authorization": headers["Authorization"]}
    r = await client.get(
        f"{STORAGE_API}/b/{quote(bucket, safe='')}/o/{_object_path(obj)}",
        headers=media_headers,
        params={"alt": "media"},
    )
    r.raise_for_status()
    raw = r.content
    content_type = r.headers.get("content-type") or "application/octet-stream"
    if node.props.download_as_binary:
        return NodeResult(
            success=True,
            output_data={
                "bucket": bucket,
                "name": obj,
                "content_base64": base64.b64encode(raw).decode("ascii"),
                "content_length": len(raw),
                "contentType": content_type,
            },
        )
    # Best-effort UTF-8 decode. Fall back to base64 if it isn't text —
    # we don't want to silently lose data for binary blobs the user
    # forgot to mark binary.
    try:
        text = raw.decode("utf-8")
        return NodeResult(
            success=True,
            output_data={
                "bucket": bucket,
                "name": obj,
                "text": text,
                "content_length": len(raw),
                "contentType": content_type,
            },
        )
    except UnicodeDecodeError:
        return NodeResult(
            success=True,
            output_data={
                "bucket": bucket,
                "name": obj,
                "content_base64": base64.b64encode(raw).decode("ascii"),
                "content_length": len(raw),
                "contentType": content_type,
                "_note": "Content was not valid UTF-8 — returned as base64. Set download_as_binary to get this shape explicitly.",
            },
        )


async def _upload_object(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    obj = _require_object(node)
    if isinstance(obj, NodeResult):
        return obj

    from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

    source_url = resolve_media_field(node.props.content)
    if not source_url:
        return NodeResult(
            success=False,
            error="`content` could not be resolved to a fetchable URL.",
        )

    inferred_mime = (node.props.content_type or "").strip() or "application/octet-stream"
    async with httpx.AsyncClient(timeout=120) as fetch:
        f_resp = await fetch.get(source_url)
        f_resp.raise_for_status()
        raw_bytes = f_resp.content
        ct = f_resp.headers.get("content-type")
        if ct and not node.props.content_type:
            inferred_mime = ct.split(";")[0].strip()

    # Build the object metadata. We always want to send a metadata
    # part if the user supplied cache-control / custom metadata, so we
    # always use the multipart wrapper — simpler than branching.
    metadata: dict[str, Any] = {"name": obj, "contentType": inferred_mime}
    if node.props.cache_control:
        metadata["cacheControl"] = node.props.cache_control.strip()
    custom_meta = _coerce_json_field(node.props.metadata)
    if isinstance(custom_meta, dict) and custom_meta:
        metadata["metadata"] = {str(k): str(v) for k, v in custom_meta.items()}

    boundary = "fuse-gcs-upload-boundary"
    body_bytes = (
        (
            f"--{boundary}\r\n"
            f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{json.dumps(metadata)}\r\n"
            f"--{boundary}\r\n"
            f"Content-Type: {inferred_mime}\r\n\r\n"
        ).encode()
        + raw_bytes
        + f"\r\n--{boundary}--".encode()
    )
    upload_headers = {
        "Authorization": headers["Authorization"],
        "Content-Type": f"multipart/related; boundary={boundary}",
    }
    r = await client.post(
        f"{UPLOAD_API}/b/{quote(bucket, safe='')}/o",
        headers=upload_headers,
        params={"uploadType": "multipart"},
        content=body_bytes,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _delete_object(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    obj = _require_object(node)
    if isinstance(obj, NodeResult):
        return obj
    r = await client.delete(
        f"{STORAGE_API}/b/{quote(bucket, safe='')}/o/{_object_path(obj)}",
        headers=headers,
    )
    r.raise_for_status()
    return NodeResult(
        success=True,
        output_data={"bucket": bucket, "name": obj, "deleted": True},
    )


async def _copy_object(
    node: GoogleCloudStorageNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    bucket = _require_bucket(node)
    if isinstance(bucket, NodeResult):
        return bucket
    obj = _require_object(node)
    if isinstance(obj, NodeResult):
        return obj
    dst_bucket = (node.props.destination_bucket or "").strip()
    dst_obj = (node.props.destination_object or "").strip()
    if not dst_bucket:
        return NodeResult(success=False, error="`destination_bucket` is required.")
    if not dst_obj:
        return NodeResult(success=False, error="`destination_object` is required.")
    r = await client.post(
        (
            f"{STORAGE_API}/b/{quote(bucket, safe='')}/o/{_object_path(obj)}/"
            f"copyTo/b/{quote(dst_bucket, safe='')}/o/{_object_path(dst_obj)}"
        ),
        headers=headers,
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


_HANDLERS: dict[str, Any] = {
    "list_buckets": _list_buckets,
    "get_bucket": _get_bucket,
    "create_bucket": _create_bucket,
    "delete_bucket": _delete_bucket,
    "list_objects": _list_objects,
    "get_object_metadata": _get_object_metadata,
    "download_object": _download_object,
    "upload_object": _upload_object,
    "delete_object": _delete_object,
    "copy_object": _copy_object,
}

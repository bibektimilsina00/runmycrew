"""Unit tests for Phase 4.11 notion + confluence webhooks.

Focus areas:
  - challenge_body_key short-circuit (Notion URL verification)
  - Notion payload_shape hoists entity + data.parent
  - Confluence payload_shape hoists page/space/comment/attachment
  - Both cover full sim event set
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from apps.api.app.features.webhooks.service import WebhookService

# Import the webhook node modules so `build_webhook_trigger()` runs at
# import time and registers the manifest with the webhook manifest
# registry. Without this, tests that reach into the service by
# `provider` string fail with a 404.
from apps.api.app.node_system.nodes.atlassian.confluence import (
    confluence_webhook as _conf_wh,  # noqa: F401
)
from apps.api.app.node_system.nodes.atlassian.confluence.webhook_manifest import (
    MANIFEST as CONFLUENCE,
)
from apps.api.app.node_system.nodes.atlassian.confluence.webhook_manifest import (
    _shape as confluence_shape,
)
from apps.api.app.node_system.nodes.notion import (
    notion_webhook as _notion_wh,  # noqa: F401
)
from apps.api.app.node_system.nodes.notion.webhook_manifest import (
    MANIFEST as NOTION,
)
from apps.api.app.node_system.nodes.notion.webhook_manifest import (
    _shape as notion_shape,
)

# ── challenge_body_key short-circuit ────────────────────────────────


@pytest.mark.anyio
async def test_notion_challenge_echoes_token_without_signature() -> None:
    """First delivery from Notion carries `{verification_token: ...}`
    and no signature — the receiver must echo the token so Notion
    accepts the endpoint. Runs BEFORE signature verification since the
    token IS the shared secret being provisioned."""
    workflow = MagicMock()
    workflow.id = uuid4()
    workflow.graph = {
        "nodes": [
            {
                "id": "n1",
                "type": "trigger.notion_webhook",
                "data": {"properties": {"secret": ""}},  # not yet configured
            }
        ]
    }

    wf_repo = MagicMock()
    wf_repo.get_by_id = AsyncMock(return_value=workflow)

    svc = WebhookService(db=MagicMock())
    from apps.api.app.features.webhooks import service as svc_module

    orig_repo_class = svc_module.WorkflowRepository
    svc_module.WorkflowRepository = MagicMock(return_value=wf_repo)  # type: ignore[assignment]
    try:
        body = json.dumps({"verification_token": "secret_XYZ"}).encode()
        result = await svc.dispatch(
            provider="notion_webhook",
            workflow_id=str(workflow.id),
            node_id="n1",
            raw_body=body,
            headers={},
            url="https://example.com/api/v1/webhooks/notion_webhook/x/n1",
        )
    finally:
        svc_module.WorkflowRepository = orig_repo_class  # type: ignore[assignment]

    # Notion expects the token echoed back — that's how it pins the
    # endpoint. Any other response shape would fail the verification
    # handshake and the webhook would never come back up.
    assert result == {"verification_token": "secret_XYZ"}


# ── manifest configuration ──────────────────────────────────────────


def test_notion_manifest_wires_challenge_and_body_path() -> None:
    assert NOTION.challenge_body_key == "verification_token"
    assert NOTION.event_body_path == "type"


def test_confluence_manifest_wires_body_path() -> None:
    assert CONFLUENCE.event_body_path == "webhookEvent"
    assert CONFLUENCE.challenge_body_key is None  # no challenge flow


# ── payload_shape smoke ─────────────────────────────────────────────


def test_notion_shape_pulls_entity_and_parent_context() -> None:
    body = {
        "type": "page.content_updated",
        "workspace_id": "ws1",
        "workspace_name": "Team",
        "authors": [{"id": "u1", "type": "person"}],
        "entity": {"id": "page1", "type": "page"},
        "data": {
            "parent": {"type": "database_id", "database_id": "db1"},
            "updated_properties": ["Status"],
        },
    }
    out = notion_shape(body, "page.content_updated", "d1")
    assert out["event"] == "page.content_updated"
    assert out["entity_id"] == "page1"
    assert out["entity_type"] == "page"
    assert out["parent_type"] == "database_id"
    assert out["parent_id"] == "db1"
    assert out["updated_properties"] == ["Status"]


def test_notion_shape_survives_delete_event_with_no_data() -> None:
    """page.deleted ships minimal envelope — no `data`. Shape must
    not crash and should still surface entity id."""
    body = {
        "type": "page.deleted",
        "entity": {"id": "page1", "type": "page"},
    }
    out = notion_shape(body, "page.deleted", "d2")
    assert out["entity_id"] == "page1"
    assert out["parent_id"] is None


def test_confluence_shape_hoists_page_space_and_modified_by() -> None:
    body = {
        "webhookEvent": "page_updated",
        "timestamp": 1720000000,
        "page": {
            "id": 12345,
            "title": "Roadmap",
            "status": "current",
            "space": {"id": 100, "spaceKey": "TEAM"},
        },
        "userAccount": {"displayName": "Alice", "accountId": "acc1"},
    }
    out = confluence_shape(body, "page_updated", "d3")
    assert out["page_id"] == 12345
    assert out["page_title"] == "Roadmap"
    assert out["space_key"] == "TEAM"
    assert out["modified_by"] == "Alice"


def test_confluence_shape_covers_comment_attachment_label() -> None:
    for body, key in [
        ({"webhookEvent": "comment_created", "comment": {"id": 1}}, "comment_id"),
        (
            {"webhookEvent": "attachment_created", "attachment": {"id": 2, "title": "x.pdf"}},
            "attachment_id",
        ),
        ({"webhookEvent": "label_added", "label": {"name": "urgent"}}, "label_name"),
    ]:
        out = confluence_shape(body, str(body["webhookEvent"]), "d")
        assert out[key] is not None


# ── event coverage ─────────────────────────────────────────────────


def test_notion_full_sim_parity() -> None:
    values = {e.value for e in NOTION.events}
    expected = {
        "page.created",
        "page.updated",
        "page.content_updated",
        "page.deleted",
        "database.created",
        "database.schema_updated",
        "database.deleted",
        "comment.created",
    }
    assert expected == values


def test_confluence_full_sim_parity() -> None:
    """Sim ships 22 confluence events. Full parity target for 4.11."""
    values = {e.value for e in CONFLUENCE.events}
    expected = {
        "page_created",
        "page_updated",
        "page_removed",
        "page_restored",
        "page_moved",
        "page_permissions_updated",
        "blog_created",
        "blog_updated",
        "blog_removed",
        "blog_restored",
        "comment_created",
        "comment_updated",
        "comment_removed",
        "attachment_created",
        "attachment_updated",
        "attachment_removed",
        "label_added",
        "label_removed",
        "space_created",
        "space_updated",
        "space_removed",
        "user_created",
    }
    assert expected == values

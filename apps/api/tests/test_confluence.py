"""Unit tests for the Confluence integration (Phase 4.4).

Covers the flatteners for page / blog / comment / space payloads and
the basic action-node registration. Wire-level tests aren't included —
Confluence auth is Basic against a per-customer host, so integration
tests would need a live Atlassian site.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.confluence.trigger_manifest import (
    _flatten_blog,
    _flatten_comment,
    _flatten_page,
    _flatten_space,
)


def test_page_flatten_hoists_version_and_web_url() -> None:
    """version.number, version.createdAt, and _links.webui are what
    downstream nodes actually want — the raw envelope buries them."""
    page = {
        "id": "12345",
        "title": "Roadmap",
        "spaceId": "s1",
        "parentId": "p1",
        "status": "current",
        "authorId": "u1",
        "createdAt": "2026-07-01T09:00:00Z",
        "version": {"number": 3, "createdAt": "2026-07-04T12:00:00Z", "authorId": "u1"},
        "_links": {"webui": "/spaces/S/pages/12345"},
    }
    out = _flatten_page(page)
    assert out["id"] == "12345"
    assert out["title"] == "Roadmap"
    assert out["version_number"] == 3
    assert out["version_created_at"] == "2026-07-04T12:00:00Z"
    assert out["web_url"] == "/spaces/S/pages/12345"


def test_blog_flatten_same_shape_as_page() -> None:
    """Blog posts share Confluence's page shape (parent_id absent) —
    flatten mirrors that so downstream code can treat them the same."""
    blog = {
        "id": "b1",
        "title": "Ship notes",
        "spaceId": "s1",
        "status": "current",
        "version": {"number": 1, "createdAt": "2026-07-04T12:00:00Z"},
    }
    out = _flatten_blog(blog)
    assert out["id"] == "b1"
    assert out["version_number"] == 1
    assert out["space_id"] == "s1"


def test_comment_flatten_pulls_body_storage_text() -> None:
    """Comment body is nested: {body: {storage: {value: '<p>...</p>'}}}.
    Downstream nodes need the storage-format value directly."""
    comment = {
        "id": "c1",
        "pageId": "12345",
        "status": "current",
        "body": {"storage": {"value": "<p>hello</p>"}},
        "version": {"authorId": "u1", "createdAt": "2026-07-04T13:00:00Z"},
        "createdAt": "2026-07-04T13:00:00Z",
    }
    out = _flatten_comment(comment)
    assert out["text"] == "<p>hello</p>"
    assert out["page_id"] == "12345"


def test_comment_flatten_falls_back_to_blog_post_parent() -> None:
    """Comments on blog posts have `blogPostId` instead of `pageId`.
    The flatten treats them symmetrically so the same trigger event can
    be reused across page + blog contexts if a future variant needs it."""
    comment = {
        "id": "c2",
        "blogPostId": "b1",
        "body": {"storage": {"value": "great"}},
        "version": {"createdAt": "2026-07-04T13:00:00Z"},
    }
    out = _flatten_comment(comment)
    assert out["page_id"] == "b1"
    assert out["text"] == "great"


def test_space_flatten_carries_key_and_type() -> None:
    space = {
        "id": "s1",
        "key": "TEAM",
        "name": "Team Space",
        "type": "global",
        "status": "current",
        "authorId": "u1",
        "createdAt": "2026-01-01T00:00:00Z",
        "_links": {"webui": "/spaces/TEAM"},
    }
    out = _flatten_space(space)
    assert out["key"] == "TEAM"
    assert out["type"] == "global"
    assert out["web_url"] == "/spaces/TEAM"


def test_confluence_action_node_registers_all_ops() -> None:
    """Regression guard — a Confluence op removed from the manifest
    would silently vanish from the inspector otherwise."""
    from apps.api.app.node_system.nodes.confluence.manifest import MANIFEST

    op_ids = {o.id for o in MANIFEST.operations}
    assert {
        "list_pages",
        "get_page",
        "create_page",
        "update_page",
        "delete_page",
        "list_spaces",
        "get_space",
        "list_blog_posts",
        "create_blog_post",
        "list_comments",
    } <= op_ids


def test_confluence_credential_is_registered() -> None:
    """`confluence_api_key` credential must exist — the trigger node
    binds to it, and a missing entry breaks the credential picker."""
    from apps.api.app.credential_manager.api_keys import PROVIDERS

    assert "confluence" in PROVIDERS
    fields = {f.id for f in PROVIDERS["confluence"].fields}
    assert fields == {"email", "api_key", "base_url"}

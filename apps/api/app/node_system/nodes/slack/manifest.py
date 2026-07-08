"""Slack action node — manifest form.

Slack Web API at `https://slack.com/api`. Bearer auth from either
`slack_oauth` (`access_token`) or a manually-supplied bot token
(`api_key`). Slack ignores standard HTTP verbs and takes every op as
POST with a JSON body — the scaffold's default is POST with
`content_type="application/json"` which fits.

Ops span: messaging (send/update/delete/ephemeral/permalink), threads
+ channel history, channels CRUD, members, users + profile (status/
title), assistant suggested prompts, reactions, views (Block Kit modals
+ home), files, canvases (full CRUD + section lookup).
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.slack import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.slack",
    name=NAME,
    category="integration",
    description="Slack — messages, threads, channels, users, reactions, views, canvases.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://slack.com/api",
    credential_type=["slack_oauth", "slack_bot_token"],
    token_field=["access_token", "api_key", "bot_token"],
    auth="bearer",
    fields=[
        FieldSpec(name="channel", label="Channel ID", type="string"),
        FieldSpec(name="channel_name", label="Channel Name", type="string"),
        FieldSpec(name="user", label="User ID", type="string"),
        FieldSpec(name="text", label="Message Text", type="string"),
        FieldSpec(name="blocks", label="Blocks (JSON)", type="json", default=[]),
        FieldSpec(name="attachments", label="Attachments (JSON)", type="json", default=[]),
        FieldSpec(name="ts", label="Message Timestamp", type="string"),
        FieldSpec(name="thread_ts", label="Thread TS (reply to)", type="string"),
        FieldSpec(name="reaction", label="Reaction (emoji, no colons)", type="string"),
        FieldSpec(name="users", label="Users (comma-separated)", type="string"),
        FieldSpec(name="is_private", label="Private Channel", type="boolean", default=False),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
        FieldSpec(name="cursor", label="Cursor", type="string", mode="advanced"),
        FieldSpec(name="trigger_id", label="Trigger ID (from interaction payload)", type="string"),
        FieldSpec(name="view", label="View (JSON)", type="json", default={}),
        FieldSpec(name="view_id", label="View ID (for update)", type="string"),
        FieldSpec(name="hash", label="Hash (for view update)", type="string"),
        FieldSpec(name="file_id", label="File ID", type="string"),
        FieldSpec(name="file_content", label="File Content", type="string"),
        FieldSpec(name="filename", label="Filename", type="string"),
        FieldSpec(name="filetype", label="Filetype", type="string"),
        FieldSpec(name="file_title", label="File Title", type="string"),
        FieldSpec(name="initial_comment", label="Initial Comment", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="oldest", label="Oldest (unix ts)", type="string"),
        FieldSpec(name="latest", label="Latest (unix ts)", type="string"),
        FieldSpec(name="canvas_id", label="Canvas ID", type="string"),
        FieldSpec(name="canvas_content", label="Canvas Content (Markdown)", type="string"),
        FieldSpec(name="canvas_title", label="Canvas Title", type="string"),
        FieldSpec(name="section_id", label="Canvas Section ID", type="string"),
        FieldSpec(name="section_lookup_query", label="Section Lookup Query", type="string"),
        FieldSpec(name="profile_field", label="Profile Field", type="string"),
        FieldSpec(name="profile_value", label="Profile Value", type="string"),
        FieldSpec(name="status_text", label="Status Text", type="string"),
        FieldSpec(name="status_emoji", label="Status Emoji", type="string"),
        FieldSpec(
            name="status_expiration", label="Status Expiration (unix)", type="number", default=0
        ),
        FieldSpec(name="prompts", label="Suggested Prompts (JSON array)", type="json", default=[]),
    ],
    operations=[
        # ─── messaging ─────────────────────────────────────────────
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/chat.postMessage",
            visible_fields=["channel", "text", "blocks", "attachments", "thread_ts"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "channel": getattr(v, "channel", "") or "",
                    "text": getattr(v, "text", "") or "",
                    "blocks": getattr(v, "blocks", None) or None,
                    "attachments": getattr(v, "attachments", None) or None,
                    "thread_ts": getattr(v, "thread_ts", None) or None,
                }.items()
                if val
            },
        ),
        OpSpec(
            id="update_message",
            label="Update Message",
            method="POST",
            path="/chat.update",
            visible_fields=["channel", "ts", "text", "blocks"],
            body_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "ts": getattr(v, "ts", "") or "",
                "text": getattr(v, "text", "") or "",
                "blocks": getattr(v, "blocks", None) or None,
            },
        ),
        OpSpec(
            id="delete_message",
            label="Delete Message",
            method="POST",
            path="/chat.delete",
            visible_fields=["channel", "ts"],
            body_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "ts": getattr(v, "ts", "") or "",
            },
        ),
        OpSpec(
            id="send_ephemeral",
            label="Send Ephemeral Message",
            method="POST",
            path="/chat.postEphemeral",
            visible_fields=["channel", "user", "text", "blocks"],
            body_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "user": getattr(v, "user", "") or "",
                "text": getattr(v, "text", "") or "",
                "blocks": getattr(v, "blocks", None) or None,
            },
        ),
        OpSpec(
            id="get_permalink",
            label="Get Message Permalink",
            method="GET",
            path="/chat.getPermalink",
            visible_fields=["channel", "ts"],
            query_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "message_ts": getattr(v, "ts", "") or "",
            },
        ),
        # ─── threads + history ─────────────────────────────────────
        OpSpec(
            id="get_message",
            label="Get Single Message",
            method="GET",
            path="/conversations.history",
            visible_fields=["channel", "ts"],
            query_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "latest": getattr(v, "ts", "") or "",
                "inclusive": "true",
                "limit": 1,
            },
        ),
        OpSpec(
            id="get_thread",
            label="Get Thread (all messages)",
            method="GET",
            path="/conversations.replies",
            visible_fields=["channel", "thread_ts"],
            query_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "ts": getattr(v, "thread_ts", "") or "",
            },
        ),
        OpSpec(
            id="get_thread_replies",
            label="Get Thread Replies",
            method="GET",
            path="/conversations.replies",
            visible_fields=["channel", "thread_ts", "limit"],
            query_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "ts": getattr(v, "thread_ts", "") or "",
                "limit": int(getattr(v, "limit", 100) or 100),
            },
        ),
        OpSpec(
            id="get_channel_history",
            label="Get Channel History",
            method="GET",
            path="/conversations.history",
            visible_fields=["channel", "limit", "oldest", "latest"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "channel": getattr(v, "channel", "") or "",
                    "limit": int(getattr(v, "limit", 100) or 100),
                    "oldest": getattr(v, "oldest", None) or None,
                    "latest": getattr(v, "latest", None) or None,
                }.items()
                if val
            },
        ),
        # ─── channels ──────────────────────────────────────────────
        OpSpec(
            id="list_channels",
            label="List Channels",
            method="GET",
            path="/conversations.list",
            visible_fields=["limit", "cursor"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "limit": int(getattr(v, "limit", 100) or 100),
                    "cursor": getattr(v, "cursor", None) or None,
                    "types": "public_channel,private_channel",
                }.items()
                if val
            },
        ),
        OpSpec(
            id="get_channel_info",
            label="Get Channel Info",
            method="GET",
            path="/conversations.info",
            visible_fields=["channel"],
            query_builder=lambda v: {"channel": getattr(v, "channel", "") or ""},
        ),
        OpSpec(
            id="create_channel",
            label="Create Channel",
            method="POST",
            path="/conversations.create",
            visible_fields=["channel_name", "is_private"],
            body_builder=lambda v: {
                "name": getattr(v, "channel_name", "") or "",
                "is_private": bool(getattr(v, "is_private", False)),
            },
        ),
        OpSpec(
            id="list_members",
            label="List Channel Members",
            method="GET",
            path="/conversations.members",
            visible_fields=["channel", "limit"],
            query_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "limit": int(getattr(v, "limit", 100) or 100),
            },
        ),
        OpSpec(
            id="invite_to_channel",
            label="Invite Users to Channel",
            method="POST",
            path="/conversations.invite",
            visible_fields=["channel", "users"],
            body_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "users": getattr(v, "users", "") or "",
            },
        ),
        OpSpec(
            id="create_conversation",
            label="Open DM / Multi-DM",
            method="POST",
            path="/conversations.open",
            visible_fields=["users"],
            body_builder=lambda v: {"users": getattr(v, "users", "") or ""},
        ),
        # ─── users ─────────────────────────────────────────────────
        OpSpec(
            id="list_users",
            label="List Users",
            method="GET",
            path="/users.list",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 100) or 100)},
        ),
        OpSpec(
            id="get_user_info",
            label="Get User Info",
            method="GET",
            path="/users.info",
            visible_fields=["user"],
            query_builder=lambda v: {"user": getattr(v, "user", "") or ""},
        ),
        OpSpec(
            id="get_user_presence",
            label="Get User Presence",
            method="GET",
            path="/users.getPresence",
            visible_fields=["user"],
            query_builder=lambda v: {"user": getattr(v, "user", "") or ""},
        ),
        OpSpec(
            id="lookup_by_email",
            label="Look Up User by Email",
            method="GET",
            path="/users.lookupByEmail",
            visible_fields=["email"],
            query_builder=lambda v: {"email": getattr(v, "email", "") or ""},
        ),
        # ─── profile ───────────────────────────────────────────────
        OpSpec(
            id="set_status",
            label="Set User Status",
            method="POST",
            path="/users.profile.set",
            visible_fields=["user", "status_text", "status_emoji", "status_expiration"],
            body_builder=lambda v: {
                "user": getattr(v, "user", None) or None,
                "profile": {
                    "status_text": getattr(v, "status_text", "") or "",
                    "status_emoji": getattr(v, "status_emoji", "") or "",
                    "status_expiration": int(getattr(v, "status_expiration", 0) or 0),
                },
            },
        ),
        OpSpec(
            id="set_title",
            label="Set User Title",
            method="POST",
            path="/users.profile.set",
            visible_fields=["user", "profile_value"],
            body_builder=lambda v: {
                "user": getattr(v, "user", None) or None,
                "profile": {"title": getattr(v, "profile_value", "") or ""},
            },
        ),
        OpSpec(
            id="set_suggested_prompts",
            label="Set Suggested Prompts (assistant)",
            method="POST",
            path="/assistant.threads.setSuggestedPrompts",
            visible_fields=["channel", "thread_ts", "prompts"],
            body_builder=lambda v: {
                "channel_id": getattr(v, "channel", "") or "",
                "thread_ts": getattr(v, "thread_ts", "") or "",
                "prompts": getattr(v, "prompts", []) or [],
            },
        ),
        # ─── reactions ─────────────────────────────────────────────
        OpSpec(
            id="add_reaction",
            label="Add Reaction",
            method="POST",
            path="/reactions.add",
            visible_fields=["channel", "ts", "reaction"],
            body_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "timestamp": getattr(v, "ts", "") or "",
                "name": getattr(v, "reaction", "") or "",
            },
        ),
        OpSpec(
            id="remove_reaction",
            label="Remove Reaction",
            method="POST",
            path="/reactions.remove",
            visible_fields=["channel", "ts", "reaction"],
            body_builder=lambda v: {
                "channel": getattr(v, "channel", "") or "",
                "timestamp": getattr(v, "ts", "") or "",
                "name": getattr(v, "reaction", "") or "",
            },
        ),
        # ─── views (Block Kit modals + home) ───────────────────────
        OpSpec(
            id="open_view",
            label="Open View (modal)",
            method="POST",
            path="/views.open",
            visible_fields=["trigger_id", "view"],
            body_builder=lambda v: {
                "trigger_id": getattr(v, "trigger_id", "") or "",
                "view": getattr(v, "view", None) or {},
            },
        ),
        OpSpec(
            id="push_view",
            label="Push View (modal stack)",
            method="POST",
            path="/views.push",
            visible_fields=["trigger_id", "view"],
            body_builder=lambda v: {
                "trigger_id": getattr(v, "trigger_id", "") or "",
                "view": getattr(v, "view", None) or {},
            },
        ),
        OpSpec(
            id="update_view",
            label="Update View",
            method="POST",
            path="/views.update",
            visible_fields=["view_id", "hash", "view"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "view_id": getattr(v, "view_id", "") or "",
                    "hash": getattr(v, "hash", None) or None,
                    "view": getattr(v, "view", None) or {},
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="publish_view",
            label="Publish Home Tab View",
            method="POST",
            path="/views.publish",
            visible_fields=["user", "view", "hash"],
            body_builder=lambda v: {
                "user_id": getattr(v, "user", "") or "",
                "view": getattr(v, "view", None) or {},
                "hash": getattr(v, "hash", None) or None,
            },
        ),
        # ─── files ─────────────────────────────────────────────────
        OpSpec(
            id="upload_file",
            label="Upload File (getUploadURL flow — v2)",
            method="POST",
            path="/files.getUploadURLExternal",
            visible_fields=["filename", "file_content"],
            body_builder=lambda v: {
                "filename": getattr(v, "filename", "") or "",
                "length": len(getattr(v, "file_content", "") or ""),
            },
        ),
        OpSpec(
            id="download",
            label="Get File Info (for download)",
            method="GET",
            path="/files.info",
            visible_fields=["file_id"],
            query_builder=lambda v: {"file": getattr(v, "file_id", "") or ""},
        ),
        # ─── canvases ──────────────────────────────────────────────
        OpSpec(
            id="canvas",
            label="Create Canvas (standalone)",
            method="POST",
            path="/canvases.create",
            visible_fields=["canvas_title", "canvas_content"],
            body_builder=lambda v: {
                "title": getattr(v, "canvas_title", "") or "",
                "document_content": {
                    "type": "markdown",
                    "markdown": getattr(v, "canvas_content", "") or "",
                },
            },
        ),
        OpSpec(
            id="create_channel_canvas",
            label="Create Channel Canvas",
            method="POST",
            path="/conversations.canvases.create",
            visible_fields=["channel", "canvas_content"],
            body_builder=lambda v: {
                "channel_id": getattr(v, "channel", "") or "",
                "document_content": {
                    "type": "markdown",
                    "markdown": getattr(v, "canvas_content", "") or "",
                },
            },
        ),
        OpSpec(
            id="get_canvas",
            label="Get Canvas (via files.info)",
            method="GET",
            path="/files.info",
            visible_fields=["canvas_id"],
            query_builder=lambda v: {"file": getattr(v, "canvas_id", "") or ""},
        ),
        OpSpec(
            id="edit_canvas",
            label="Edit Canvas",
            method="POST",
            path="/canvases.edit",
            visible_fields=["canvas_id", "canvas_content"],
            body_builder=lambda v: {
                "canvas_id": getattr(v, "canvas_id", "") or "",
                "changes": [
                    {
                        "operation": "replace",
                        "document_content": {
                            "type": "markdown",
                            "markdown": getattr(v, "canvas_content", "") or "",
                        },
                    }
                ],
            },
        ),
        OpSpec(
            id="list_canvases",
            label="List Canvases (via files.list)",
            method="GET",
            path="/files.list",
            visible_fields=[],
            query_builder=lambda v: {"types": "canvases"},
        ),
        OpSpec(
            id="lookup_canvas_sections",
            label="Look Up Canvas Sections",
            method="POST",
            path="/canvases.sections.lookup",
            visible_fields=["canvas_id", "section_lookup_query"],
            body_builder=lambda v: {
                "canvas_id": getattr(v, "canvas_id", "") or "",
                "criteria": {"contains_text": getattr(v, "section_lookup_query", "") or ""},
            },
        ),
        OpSpec(
            id="delete_canvas",
            label="Delete Canvas",
            method="POST",
            path="/canvases.delete",
            visible_fields=["canvas_id"],
            body_builder=lambda v: {"canvas_id": getattr(v, "canvas_id", "") or ""},
        ),
    ],
    outputs_schema=[
        {"label": "ok", "type": "boolean"},
        {"label": "data", "type": "object"},
        {"label": "ts", "type": "string"},
        {"label": "channel", "type": "string"},
    ],
    allow_error=True,
)

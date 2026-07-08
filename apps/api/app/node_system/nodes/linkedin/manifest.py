"""LinkedIn action node — manifest form.

LinkedIn v2 REST API at `https://api.linkedin.com/v2`. Bearer auth.
Two key surfaces:
  - Member profile + email (OpenID Connect endpoints)
  - Posts on behalf of the member (`w_member_social` scope)

The member URN (`urn:li:person:{id}`) is the "actor" for posts. We
resolve it from userinfo on the first call — user pastes it into
the manifest field on the node for now.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.linkedin",
    name="LinkedIn",
    category="integration",
    description="LinkedIn — profile info + post updates as your member account.",
    icon_slug="linkedin",
    color="#ffffff",
    base_url="https://api.linkedin.com",
    credential_type="linkedin_oauth",
    token_field=["access_token"],
    auth="bearer",
    # LinkedIn requires an X-Restli-Protocol-Version header on v2
    # endpoints; without it, JSON serialization defaults to Rest.li
    # protocol 1.0 which is stricter.
    extra_headers={"X-Restli-Protocol-Version": "2.0.0", "LinkedIn-Version": "202410"},
    fields=[
        FieldSpec(
            name="author_urn",
            label="Author URN",
            type="string",
            placeholder="urn:li:person:abc123",
            description="Your LinkedIn member URN. Fetch once via Get Userinfo, then paste here.",
        ),
        FieldSpec(name="post_id", label="Post ID (URN)", type="string"),
        FieldSpec(name="commentary", label="Post commentary", type="string"),
        FieldSpec(
            name="visibility",
            label="Visibility",
            type="options",
            default="PUBLIC",
            mode="advanced",
            options=[
                {"label": "Public", "value": "PUBLIC"},
                {"label": "Connections", "value": "CONNECTIONS"},
                {"label": "Logged-in members", "value": "LOGGED_IN"},
            ],
        ),
    ],
    operations=[
        OpSpec(
            id="get_userinfo",
            label="Get Userinfo (OIDC)",
            method="GET",
            path="/v2/userinfo",
        ),
        OpSpec(
            id="get_me",
            label="Get Member Profile",
            method="GET",
            path="/v2/me",
        ),
        OpSpec(
            id="create_post",
            label="Create Post",
            method="POST",
            path="/rest/posts",
            visible_fields=["author_urn", "commentary", "visibility"],
            body_builder=lambda v: {
                "author": getattr(v, "author_urn", None) or "",
                "commentary": getattr(v, "commentary", None) or "",
                "visibility": getattr(v, "visibility", None) or "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
            },
        ),
        OpSpec(
            id="delete_post",
            label="Delete Post",
            method="DELETE",
            path="/rest/posts/{post_id}",
            visible_fields=["post_id"],
            success_payload_template={"deleted": True, "post_id": "{post_id}"},
        ),
    ],
    outputs_schema=[
        {"label": "sub", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "id", "type": "string"},
        {"label": "x-restli-id", "type": "string"},
    ],
    allow_error=True,
)

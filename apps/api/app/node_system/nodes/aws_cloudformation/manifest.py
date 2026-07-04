"""AWS CloudFormation action node — manifest form.

Query protocol at `https://cloudformation.{region}.amazonaws.com/`.
Version `2010-05-15`. Stack lifecycle + resource introspection.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://cloudformation.{region}.amazonaws.com/"
_VERSION = "2010-05-15"


def _q(action: str, **params) -> dict:
    return {
        "Action": action,
        "Version": _VERSION,
        **{k: v for k, v in params.items() if v is not None},
    }


MANIFEST = ProviderManifest(
    type="action.aws_cloudformation",
    name="AWS CloudFormation",
    category="integration",
    description="AWS CloudFormation — stacks, resources, change sets.",
    icon_slug="aws-cloudformation",
    color="#1c1c1c",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="cloudformation",
    aws_default_region="us-east-1",
    content_type="application/x-www-form-urlencoded",
    fields=[
        FieldSpec(name="stack_name", label="Stack Name", type="string"),
        FieldSpec(name="template_body", label="Template Body (JSON/YAML)", type="string"),
        FieldSpec(name="template_url", label="Template URL (S3)", type="string", mode="advanced"),
        FieldSpec(name="parameters", label="Parameters (JSON array)", type="json", mode="advanced"),
        FieldSpec(
            name="capabilities", label="Capabilities (JSON array)", type="json", mode="advanced"
        ),
        FieldSpec(name="change_set_name", label="Change Set Name", type="string"),
        FieldSpec(name="next_token", label="Next Token", type="string", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_stacks",
            label="List Stacks",
            method="POST",
            path=_HOST,
            visible_fields=["next_token"],
            body_builder=lambda v: _q(
                "ListStacks",
                NextToken=getattr(v, "next_token", None),
            ),
        ),
        OpSpec(
            id="describe_stacks",
            label="Describe Stacks",
            method="POST",
            path=_HOST,
            visible_fields=["stack_name"],
            body_builder=lambda v: _q(
                "DescribeStacks",
                StackName=getattr(v, "stack_name", None),
            ),
        ),
        OpSpec(
            id="describe_stack_resources",
            label="Describe Stack Resources",
            method="POST",
            path=_HOST,
            visible_fields=["stack_name"],
            body_builder=lambda v: _q(
                "DescribeStackResources",
                StackName=getattr(v, "stack_name", None) or "",
            ),
        ),
        OpSpec(
            id="create_stack",
            label="Create Stack",
            method="POST",
            path=_HOST,
            visible_fields=["stack_name", "template_body", "template_url", "capabilities"],
            body_builder=lambda v: _q(
                "CreateStack",
                StackName=getattr(v, "stack_name", None) or "",
                TemplateBody=getattr(v, "template_body", None),
                TemplateURL=getattr(v, "template_url", None),
                Capabilities=(
                    ",".join(v.capabilities) if getattr(v, "capabilities", None) else None
                ),
            ),
        ),
        OpSpec(
            id="update_stack",
            label="Update Stack",
            method="POST",
            path=_HOST,
            visible_fields=["stack_name", "template_body", "template_url"],
            body_builder=lambda v: _q(
                "UpdateStack",
                StackName=getattr(v, "stack_name", None) or "",
                TemplateBody=getattr(v, "template_body", None),
                TemplateURL=getattr(v, "template_url", None),
            ),
        ),
        OpSpec(
            id="delete_stack",
            label="Delete Stack",
            method="POST",
            path=_HOST,
            visible_fields=["stack_name"],
            body_builder=lambda v: _q(
                "DeleteStack",
                StackName=getattr(v, "stack_name", None) or "",
            ),
            success_payload_template={"deleted": True, "stack_name": "{stack_name}"},
        ),
        OpSpec(
            id="create_change_set",
            label="Create Change Set",
            method="POST",
            path=_HOST,
            visible_fields=["stack_name", "change_set_name", "template_body", "template_url"],
            body_builder=lambda v: _q(
                "CreateChangeSet",
                StackName=getattr(v, "stack_name", None) or "",
                ChangeSetName=getattr(v, "change_set_name", None) or "",
                TemplateBody=getattr(v, "template_body", None),
                TemplateURL=getattr(v, "template_url", None),
            ),
        ),
        OpSpec(
            id="describe_change_set",
            label="Describe Change Set",
            method="POST",
            path=_HOST,
            visible_fields=["stack_name", "change_set_name"],
            body_builder=lambda v: _q(
                "DescribeChangeSet",
                StackName=getattr(v, "stack_name", None) or "",
                ChangeSetName=getattr(v, "change_set_name", None) or "",
            ),
        ),
        OpSpec(
            id="execute_change_set",
            label="Execute Change Set",
            method="POST",
            path=_HOST,
            visible_fields=["stack_name", "change_set_name"],
            body_builder=lambda v: _q(
                "ExecuteChangeSet",
                StackName=getattr(v, "stack_name", None) or "",
                ChangeSetName=getattr(v, "change_set_name", None) or "",
            ),
        ),
    ],
    outputs_schema=[
        {"label": "Stacks", "type": "array"},
        {"label": "StackResources", "type": "array"},
        {"label": "StackId", "type": "string"},
        {"label": "ChangeSetId", "type": "string"},
        {"label": "ResponseMetadata", "type": "object"},
    ],
    allow_error=True,
)

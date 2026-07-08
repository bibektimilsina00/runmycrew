"""AWS SQS action node — manifest form.

SQS's JSON protocol: POST `https://sqs.{region}.amazonaws.com/` with
`X-Amz-Target: AmazonSQS.<Action>` + JSON body. Content-Type is
`application/x-amz-json-1.0`. Every op ships its own X-Amz-Target
via the per-op `extra_headers` field.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_SQS_HOST = "https://sqs.{region}.amazonaws.com/"

MANIFEST = ProviderManifest(
    type="action.aws_sqs",
    name="Amazon SQS",
    category="integration",
    description="Amazon SQS — queues + messages via SigV4.",
    icon_slug="aws-sqs",
    color="#ffffff",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="sqs",
    aws_default_region="us-east-1",
    content_type="application/x-amz-json-1.0",
    fields=[
        FieldSpec(name="queue_url", label="Queue URL", type="string"),
        FieldSpec(name="queue_name", label="Queue Name", type="string"),
        FieldSpec(name="message_body", label="Message Body", type="string"),
        FieldSpec(
            name="max_messages", label="Max Messages", type="number", default=10, mode="advanced"
        ),
        FieldSpec(
            name="wait_seconds", label="Wait Seconds", type="number", default=0, mode="advanced"
        ),
        FieldSpec(name="receipt_handle", label="Receipt Handle", type="string"),
        FieldSpec(
            name="delay_seconds",
            label="Delay Seconds",
            type="number",
            default=0,
            mode="advanced",
        ),
        FieldSpec(name="attributes", label="Attributes (JSON)", type="json", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_queues",
            label="List Queues",
            method="POST",
            path=_SQS_HOST,
            extra_headers={"X-Amz-Target": "AmazonSQS.ListQueues"},
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="create_queue",
            label="Create Queue",
            method="POST",
            path=_SQS_HOST,
            extra_headers={"X-Amz-Target": "AmazonSQS.CreateQueue"},
            visible_fields=["queue_name", "attributes"],
            body_builder=lambda v: {
                "QueueName": getattr(v, "queue_name", None) or "",
                "Attributes": getattr(v, "attributes", None) or {},
            },
        ),
        OpSpec(
            id="delete_queue",
            label="Delete Queue",
            method="POST",
            path=_SQS_HOST,
            extra_headers={"X-Amz-Target": "AmazonSQS.DeleteQueue"},
            visible_fields=["queue_url"],
            body_builder=lambda v: {"QueueUrl": getattr(v, "queue_url", None) or ""},
            success_payload_template={"deleted": True, "queue": "{queue_url}"},
        ),
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path=_SQS_HOST,
            extra_headers={"X-Amz-Target": "AmazonSQS.SendMessage"},
            visible_fields=["queue_url", "message_body", "delay_seconds"],
            body_builder=lambda v: {
                "QueueUrl": getattr(v, "queue_url", None) or "",
                "MessageBody": getattr(v, "message_body", None) or "",
                "DelaySeconds": int(getattr(v, "delay_seconds", 0) or 0),
            },
        ),
        OpSpec(
            id="receive_messages",
            label="Receive Messages",
            method="POST",
            path=_SQS_HOST,
            extra_headers={"X-Amz-Target": "AmazonSQS.ReceiveMessage"},
            visible_fields=["queue_url", "max_messages", "wait_seconds"],
            body_builder=lambda v: {
                "QueueUrl": getattr(v, "queue_url", None) or "",
                "MaxNumberOfMessages": int(getattr(v, "max_messages", 10) or 10),
                "WaitTimeSeconds": int(getattr(v, "wait_seconds", 0) or 0),
            },
        ),
        OpSpec(
            id="delete_message",
            label="Delete Message",
            method="POST",
            path=_SQS_HOST,
            extra_headers={"X-Amz-Target": "AmazonSQS.DeleteMessage"},
            visible_fields=["queue_url", "receipt_handle"],
            body_builder=lambda v: {
                "QueueUrl": getattr(v, "queue_url", None) or "",
                "ReceiptHandle": getattr(v, "receipt_handle", None) or "",
            },
            success_payload_template={"deleted": True, "receipt_handle": "{receipt_handle}"},
        ),
        OpSpec(
            id="get_queue_attributes",
            label="Get Queue Attributes",
            method="POST",
            path=_SQS_HOST,
            extra_headers={"X-Amz-Target": "AmazonSQS.GetQueueAttributes"},
            visible_fields=["queue_url"],
            body_builder=lambda v: {
                "QueueUrl": getattr(v, "queue_url", None) or "",
                "AttributeNames": ["All"],
            },
        ),
    ],
    outputs_schema=[
        {"label": "MessageId", "type": "string"},
        {"label": "QueueUrl", "type": "string"},
        {"label": "QueueUrls", "type": "array"},
        {"label": "Messages", "type": "array"},
        {"label": "Attributes", "type": "object"},
    ],
    allow_error=True,
)

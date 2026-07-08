from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.slack import COLOR, ICON_SLUG, NAME


class SlackTriggerProperties(BaseModel):
    authentication: str = "runmycrew_bot"
    bot_token: str | None = None
    event_type: str = "message"
    channel: str | None = None


class SlackTriggerNode(BaseNode[SlackTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.slack",
            name=NAME,
            category="trigger",
            description="Listen for any Slack event: messages, reactions, channel changes, app interactions, and more.",
            icon=ICON_SLUG,
            color=COLOR,
            properties=[
                {
                    "name": "authentication",
                    "label": "Authentication",
                    "type": "options",
                    "default": "runmycrew_bot",
                    "options": [
                        {"label": "RunMyCrew Bot (OAuth)", "value": "runmycrew_bot"},
                        {"label": "Custom Bot (Token)", "value": "custom_bot"},
                    ],
                },
                {
                    "name": "credential",
                    "label": "Slack Account",
                    "type": "credential",
                    "credentialType": "slack_oauth",
                    "required": True,
                    "condition": {"field": "authentication", "value": "runmycrew_bot"},
                },
                {
                    "name": "bot_token",
                    "label": "Bot Token",
                    "type": "string",
                    "required": True,
                    "secret": True,
                    "placeholder": "xoxb-...",
                    "condition": {"field": "authentication", "value": "custom_bot"},
                },
                {
                    "name": "event_type",
                    "label": "Event Type",
                    "type": "options",
                    "default": "message",
                    "options": [
                        {"label": "New Message", "value": "message"},
                        {"label": "New Reaction", "value": "reaction_added"},
                        {"label": "Reaction Removed", "value": "reaction_removed"},
                        {"label": "Channel Created", "value": "channel_created"},
                        {"label": "Channel Archived", "value": "channel_archive"},
                        {"label": "Member Joined Channel", "value": "member_joined_channel"},
                        {"label": "Member Left Channel", "value": "member_left_channel"},
                        {"label": "User Profile Changed", "value": "user_change"},
                        {"label": "App Home Opened", "value": "app_home_opened"},
                        {"label": "Slash Command", "value": "slash_command"},
                        {"label": "Interactive Button/Menu", "value": "block_actions"},
                        {"label": "Modal Submitted", "value": "view_submission"},
                        {"label": "Modal Closed", "value": "view_closed"},
                    ],
                },
                {
                    "name": "channel",
                    "label": "Channel Filter (Optional)",
                    "type": "string",
                    "placeholder": "C1234567890",
                    "condition": {
                        "field": "event_type",
                        "value": [
                            "message",
                            "reaction_added",
                            "reaction_removed",
                            "member_joined_channel",
                            "member_left_channel",
                        ],
                    },
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "event_type", "type": "string"},
                {"label": "user", "type": "string"},
                {"label": "channel", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "ts", "type": "string"},
                {"label": "trigger_id", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="slack_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[SlackTriggerProperties]:
        return SlackTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        return NodeResult(success=True, output_data=input_data)

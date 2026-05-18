from typing import Any

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.nodes.ai.agent.agent import AgentNode
from apps.api.app.node_system.nodes.common.condition.condition import ConditionNode
from apps.api.app.node_system.nodes.common.delay.delay import DelayNode
from apps.api.app.node_system.nodes.common.json_transform.json_transform import JsonTransformNode
from apps.api.app.node_system.nodes.common.merge.merge import MergeNode
from apps.api.app.node_system.nodes.common.set_variable.set_variable import SetVariableNode
from apps.api.app.node_system.nodes.common.switch.switch import SwitchNode
from apps.api.app.node_system.nodes.common.trigger.manual import TriggerNode
from apps.api.app.node_system.nodes.http.request.request import HttpRequestNode
from apps.api.app.node_system.nodes.http.webhook.webhook import WebhookTriggerNode
from apps.api.app.node_system.nodes.slack.slack_node import SlackNode
from apps.api.app.node_system.nodes.slack.slack_trigger import SlackTriggerNode


class NodeRegistry:
    def __init__(self):
        self._nodes: dict[str, type[BaseNode]] = {}

    def register(self, node_class: type[BaseNode]) -> None:
        metadata = node_class.get_metadata()
        self._nodes[metadata.type] = node_class

    def get_node(self, node_type: str) -> type[BaseNode]:
        if node_type not in self._nodes:
            raise ValueError(f"Node type '{node_type}' not registered")
        return self._nodes[node_type]

    def list_nodes(self) -> list[dict[str, Any]]:
        return [cls.get_metadata().model_dump() for cls in self._nodes.values()]


node_registry = NodeRegistry()

# Register builtin nodes
node_registry.register(TriggerNode)
node_registry.register(AgentNode)
node_registry.register(HttpRequestNode)
node_registry.register(WebhookTriggerNode)
node_registry.register(DelayNode)
node_registry.register(ConditionNode)
node_registry.register(SlackNode)
node_registry.register(SlackTriggerNode)
node_registry.register(SetVariableNode)
node_registry.register(JsonTransformNode)
node_registry.register(MergeNode)
node_registry.register(SwitchNode)

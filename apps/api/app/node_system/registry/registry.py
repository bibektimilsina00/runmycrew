from typing import Any

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.nodes.ai.a2a.a2a import A2ANode
from apps.api.app.node_system.nodes.ai.agent.agent import AgentNode
from apps.api.app.node_system.nodes.ai.browser_use.browser_use_node import BrowserUseNode
from apps.api.app.node_system.nodes.ai.embeddings.embeddings_node import EmbeddingsNode
from apps.api.app.node_system.nodes.ai.evaluator.evaluator import EvaluatorNode
from apps.api.app.node_system.nodes.ai.image_gen.image_gen_node import ImageGenNode
from apps.api.app.node_system.nodes.ai.knowledge.knowledge_node import KnowledgeNode
from apps.api.app.node_system.nodes.ai.llm.llm import LLMNode
from apps.api.app.node_system.nodes.ai.memory.memory_node import MemoryNode
from apps.api.app.node_system.nodes.ai.perplexity.perplexity_node import PerplexityNode
from apps.api.app.node_system.nodes.ai.stt.stt_node import STTNode
from apps.api.app.node_system.nodes.ai.thinking.thinking import ThinkingNode
from apps.api.app.node_system.nodes.ai.tts.tts_node import TTSNode
from apps.api.app.node_system.nodes.ai.vision.vision_node import VisionNode
from apps.api.app.node_system.nodes.airtable.airtable_node import AirtableNode
from apps.api.app.node_system.nodes.common.condition.condition import ConditionNode
from apps.api.app.node_system.nodes.common.cron.cron_node import CronTriggerNode
from apps.api.app.node_system.nodes.common.delay.delay import DelayNode
from apps.api.app.node_system.nodes.common.json_transform.json_transform import JsonTransformNode
from apps.api.app.node_system.nodes.common.merge.merge import MergeNode
from apps.api.app.node_system.nodes.common.set_variable.set_variable import SetVariableNode
from apps.api.app.node_system.nodes.common.switch.switch import SwitchNode
from apps.api.app.node_system.nodes.common.trigger.manual import TriggerNode
from apps.api.app.node_system.nodes.common.wait.wait import WaitNode
from apps.api.app.node_system.nodes.db.dynamodb.dynamodb import DynamoDBNode
from apps.api.app.node_system.nodes.db.mongodb.mongodb import MongoDBNode
from apps.api.app.node_system.nodes.db.mysql.mysql import MySQLNode
from apps.api.app.node_system.nodes.db.neo4j.neo4j import Neo4jNode
from apps.api.app.node_system.nodes.db.postgres.postgres import PostgresNode
from apps.api.app.node_system.nodes.discord.discord_node import DiscordNode
from apps.api.app.node_system.nodes.firecrawl.firecrawl_node import FirecrawlNode
from apps.api.app.node_system.nodes.ga4.ga4_node import GoogleAnalyticsNode
from apps.api.app.node_system.nodes.gcalendar.gcal_node import GCalNode
from apps.api.app.node_system.nodes.gcalendar.gcal_trigger import GCalTriggerNode
from apps.api.app.node_system.nodes.gchat.gchat_node import GoogleChatNode
from apps.api.app.node_system.nodes.gchat.gchat_trigger import GoogleChatTriggerNode
from apps.api.app.node_system.nodes.gcs.gcs_node import GoogleCloudStorageNode
from apps.api.app.node_system.nodes.gdocs.gdocs_node import GoogleDocsNode
from apps.api.app.node_system.nodes.gdrive.gdrive_node import GDriveNode
from apps.api.app.node_system.nodes.gdrive.gdrive_trigger import GDriveTriggerNode
from apps.api.app.node_system.nodes.gforms.gforms_node import GoogleFormsNode
from apps.api.app.node_system.nodes.gforms.gforms_trigger import GoogleFormsTriggerNode
from apps.api.app.node_system.nodes.github.github_node import GitHubNode
from apps.api.app.node_system.nodes.gitlab.gitlab_webhook import GitLabWebhookTriggerNode
from apps.api.app.node_system.nodes.gmail.gmail_node import GmailNode
from apps.api.app.node_system.nodes.gmail.gmail_trigger import GmailTriggerNode
from apps.api.app.node_system.nodes.google_sheets.google_sheets import GoogleSheetsNode
from apps.api.app.node_system.nodes.google_sheets.google_sheets_trigger import (
    GoogleSheetsTriggerNode,
)
from apps.api.app.node_system.nodes.gpeople.gpeople_node import GooglePeopleNode
from apps.api.app.node_system.nodes.gpeople.gpeople_trigger import GooglePeopleTriggerNode
from apps.api.app.node_system.nodes.gsc.gsc_node import GoogleSearchConsoleNode
from apps.api.app.node_system.nodes.gslides.gslides_node import GoogleSlidesNode
from apps.api.app.node_system.nodes.gtasks.gtasks_node import GoogleTasksNode
from apps.api.app.node_system.nodes.gtasks.gtasks_trigger import GoogleTasksTriggerNode
from apps.api.app.node_system.nodes.gyt.gyt_node import GoogleYouTubeNode
from apps.api.app.node_system.nodes.gyt.gyt_trigger import GoogleYouTubeTriggerNode
from apps.api.app.node_system.nodes.http.request.request import HttpRequestNode
from apps.api.app.node_system.nodes.http.webhook.webhook import WebhookTriggerNode
from apps.api.app.node_system.nodes.hubspot.hubspot_node import HubSpotNode
from apps.api.app.node_system.nodes.jira.jira_node import JiraNode
from apps.api.app.node_system.nodes.linear.linear_node import LinearNode
from apps.api.app.node_system.nodes.logic.code.code_node import CodeNode
from apps.api.app.node_system.nodes.logic.do_while.do_while import DoWhileNode
from apps.api.app.node_system.nodes.logic.for_loop.for_loop import ForLoopNode
from apps.api.app.node_system.nodes.logic.foreach.foreach import ForEachNode
from apps.api.app.node_system.nodes.logic.human_input.human_input import HumanInputNode
from apps.api.app.node_system.nodes.logic.loop.loop_node import LoopNode
from apps.api.app.node_system.nodes.logic.sub_workflow.sub_workflow_node import SubWorkflowNode
from apps.api.app.node_system.nodes.logic.while_loop.while_loop import WhileLoopNode
from apps.api.app.node_system.nodes.meta.facebook_action import FacebookActionNode
from apps.api.app.node_system.nodes.meta.facebook_trigger import FacebookTriggerNode
from apps.api.app.node_system.nodes.meta.instagram_action import InstagramActionNode
from apps.api.app.node_system.nodes.meta.instagram_trigger import InstagramTriggerNode
from apps.api.app.node_system.nodes.meta.lead_action import LeadActionNode
from apps.api.app.node_system.nodes.meta.lead_trigger import LeadTriggerNode
from apps.api.app.node_system.nodes.meta.whatsapp_action import WhatsAppActionNode
from apps.api.app.node_system.nodes.meta.whatsapp_trigger import WhatsAppTriggerNode
from apps.api.app.node_system.nodes.notion.notion_node import NotionNode
from apps.api.app.node_system.nodes.salesforce.salesforce_node import SalesforceNode
from apps.api.app.node_system.nodes.slack.slack_node import SlackNode
from apps.api.app.node_system.nodes.slack.slack_trigger import SlackTriggerNode
from apps.api.app.node_system.nodes.stripe.stripe_node import StripeNode
from apps.api.app.node_system.nodes.telegram.telegram_node import TelegramNode


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
node_registry.register(CronTriggerNode)
node_registry.register(AgentNode)
node_registry.register(LLMNode)
node_registry.register(KnowledgeNode)
node_registry.register(VisionNode)
node_registry.register(MemoryNode)
node_registry.register(PerplexityNode)
node_registry.register(BrowserUseNode)
node_registry.register(EmbeddingsNode)
node_registry.register(TTSNode)
node_registry.register(STTNode)
node_registry.register(ImageGenNode)
node_registry.register(HttpRequestNode)
node_registry.register(WebhookTriggerNode)
node_registry.register(DelayNode)
node_registry.register(ConditionNode)
node_registry.register(SlackNode)
node_registry.register(SlackTriggerNode)
node_registry.register(GitHubNode)
node_registry.register(GitLabWebhookTriggerNode)
node_registry.register(NotionNode)
node_registry.register(AirtableNode)
node_registry.register(DiscordNode)
node_registry.register(FirecrawlNode)
node_registry.register(StripeNode)
node_registry.register(HubSpotNode)
node_registry.register(TelegramNode)
node_registry.register(GmailNode)
node_registry.register(GmailTriggerNode)
node_registry.register(GCalTriggerNode)
node_registry.register(GCalNode)
node_registry.register(GDriveTriggerNode)
node_registry.register(GDriveNode)
node_registry.register(GoogleSheetsNode)
node_registry.register(GoogleSheetsTriggerNode)
node_registry.register(GoogleDocsNode)
node_registry.register(GoogleTasksNode)
node_registry.register(GoogleTasksTriggerNode)
node_registry.register(GoogleFormsNode)
node_registry.register(GoogleFormsTriggerNode)
node_registry.register(GooglePeopleNode)
node_registry.register(GooglePeopleTriggerNode)
node_registry.register(GoogleYouTubeNode)
node_registry.register(GoogleYouTubeTriggerNode)
node_registry.register(GoogleSlidesNode)
node_registry.register(GoogleChatNode)
node_registry.register(GoogleChatTriggerNode)
node_registry.register(GoogleAnalyticsNode)
node_registry.register(GoogleSearchConsoleNode)
node_registry.register(GoogleCloudStorageNode)
node_registry.register(LinearNode)
# Meta surfaces — one consolidated trigger + action per surface
# (Instagram, Facebook/Messenger, WhatsApp, Lead Ads) carrying
# event_type / operation dropdowns. Replaces the 24 per-task nodes
# shipped in earlier phases — see service.py _TRIGGER_SPECS.
node_registry.register(InstagramTriggerNode)
node_registry.register(InstagramActionNode)
node_registry.register(FacebookTriggerNode)
node_registry.register(FacebookActionNode)
node_registry.register(LeadTriggerNode)
node_registry.register(LeadActionNode)
node_registry.register(WhatsAppTriggerNode)
node_registry.register(WhatsAppActionNode)
node_registry.register(SetVariableNode)
node_registry.register(JsonTransformNode)
node_registry.register(MergeNode)
node_registry.register(SwitchNode)
node_registry.register(WaitNode)
node_registry.register(EvaluatorNode)
node_registry.register(ThinkingNode)
node_registry.register(LoopNode)
node_registry.register(ForLoopNode)
node_registry.register(WhileLoopNode)
node_registry.register(DoWhileNode)
node_registry.register(ForEachNode)
node_registry.register(CodeNode)
node_registry.register(HumanInputNode)
node_registry.register(A2ANode)
node_registry.register(PostgresNode)
node_registry.register(MySQLNode)
node_registry.register(MongoDBNode)
node_registry.register(DynamoDBNode)
node_registry.register(Neo4jNode)
node_registry.register(JiraNode)
node_registry.register(SalesforceNode)
node_registry.register(SubWorkflowNode)

# Load tool definitions (side-effect: registers all tools in tool_registry)
import apps.api.app.node_system.tools.loader  # noqa: E402, F401

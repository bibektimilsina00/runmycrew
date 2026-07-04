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
from apps.api.app.node_system.nodes.algolia.algolia_node import AlgoliaNode
from apps.api.app.node_system.nodes.apify.apify_node import ApifyNode
from apps.api.app.node_system.nodes.asana.asana_node import AsanaNode
from apps.api.app.node_system.nodes.asana.asana_trigger import AsanaTriggerNode
from apps.api.app.node_system.nodes.attio.attio_node import AttioNode
from apps.api.app.node_system.nodes.aws_athena.aws_athena_node import AWSAthenaNode
from apps.api.app.node_system.nodes.aws_cloudformation.aws_cloudformation_node import (
    AWSCloudFormationNode,
)
from apps.api.app.node_system.nodes.aws_cloudwatch_logs.aws_cloudwatch_logs_node import (
    AWSCloudWatchLogsNode,
)
from apps.api.app.node_system.nodes.aws_iam.aws_iam_node import AWSIAMNode
from apps.api.app.node_system.nodes.aws_rds.aws_rds_node import AWSRDSNode
from apps.api.app.node_system.nodes.aws_s3.aws_s3_node import AWSS3Node
from apps.api.app.node_system.nodes.aws_secrets_manager.aws_secrets_manager_node import (
    AWSSecretsManagerNode,
)
from apps.api.app.node_system.nodes.aws_ses.aws_ses_node import AWSSESNode
from apps.api.app.node_system.nodes.aws_sqs.aws_sqs_node import AWSSQSNode
from apps.api.app.node_system.nodes.aws_sts.aws_sts_node import AWSSTSNode
from apps.api.app.node_system.nodes.azure_devops.azure_devops_webhook import (
    AzureDevOpsWebhookTriggerNode,
)
from apps.api.app.node_system.nodes.box.box_node import BoxNode
from apps.api.app.node_system.nodes.brandfetch.brandfetch_node import BrandfetchNode
from apps.api.app.node_system.nodes.calcom.calcom_node import CalcomNode
from apps.api.app.node_system.nodes.calcom.calcom_trigger import CalcomTriggerNode
from apps.api.app.node_system.nodes.calendly.calendly_node import CalendlyNode
from apps.api.app.node_system.nodes.calendly.calendly_trigger import CalendlyTriggerNode
from apps.api.app.node_system.nodes.cloudflare.cloudflare_node import CloudflareNode
from apps.api.app.node_system.nodes.common.condition.condition import ConditionNode
from apps.api.app.node_system.nodes.common.cron.cron_node import CronTriggerNode
from apps.api.app.node_system.nodes.common.delay.delay import DelayNode
from apps.api.app.node_system.nodes.common.json_transform.json_transform import JsonTransformNode
from apps.api.app.node_system.nodes.common.merge.merge import MergeNode
from apps.api.app.node_system.nodes.common.set_variable.set_variable import SetVariableNode
from apps.api.app.node_system.nodes.common.switch.switch import SwitchNode
from apps.api.app.node_system.nodes.common.trigger.manual import TriggerNode
from apps.api.app.node_system.nodes.common.wait.wait import WaitNode
from apps.api.app.node_system.nodes.customer_io.customer_io_node import CustomerIONode
from apps.api.app.node_system.nodes.db.dynamodb.dynamodb import DynamoDBNode
from apps.api.app.node_system.nodes.db.mongodb.mongodb import MongoDBNode
from apps.api.app.node_system.nodes.db.mysql.mysql import MySQLNode
from apps.api.app.node_system.nodes.db.neo4j.neo4j import Neo4jNode
from apps.api.app.node_system.nodes.db.postgres.postgres import PostgresNode
from apps.api.app.node_system.nodes.discord.discord_node import DiscordNode
from apps.api.app.node_system.nodes.docusign.docusign_node import DocuSignNode
from apps.api.app.node_system.nodes.dropbox.dropbox_node import DropboxNode
from apps.api.app.node_system.nodes.dub.dub_node import DubNode
from apps.api.app.node_system.nodes.duckduckgo.duckduckgo_node import DuckDuckGoNode
from apps.api.app.node_system.nodes.exa.exa_node import ExaNode
from apps.api.app.node_system.nodes.fathom.fathom_node import FathomNode
from apps.api.app.node_system.nodes.fathom.fathom_webhook import FathomWebhookTriggerNode
from apps.api.app.node_system.nodes.firecrawl.firecrawl_node import FirecrawlNode
from apps.api.app.node_system.nodes.fireflies.fireflies_node import FirefliesNode
from apps.api.app.node_system.nodes.fireflies.fireflies_webhook import (
    FirefliesWebhookTriggerNode,
)
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
from apps.api.app.node_system.nodes.gitlab.gitlab_trigger import GitLabTriggerNode
from apps.api.app.node_system.nodes.gitlab.gitlab_webhook import GitLabWebhookTriggerNode
from apps.api.app.node_system.nodes.gmail.gmail_node import GmailNode
from apps.api.app.node_system.nodes.gmail.gmail_trigger import GmailTriggerNode
from apps.api.app.node_system.nodes.gong.gong_node import GongNode
from apps.api.app.node_system.nodes.gong.gong_webhook import GongWebhookTriggerNode
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
from apps.api.app.node_system.nodes.hackernews.hackernews_node import HackerNewsNode
from apps.api.app.node_system.nodes.http.request.request import HttpRequestNode
from apps.api.app.node_system.nodes.http.webhook.webhook import WebhookTriggerNode
from apps.api.app.node_system.nodes.hubspot.hubspot_node import HubSpotNode
from apps.api.app.node_system.nodes.hubspot.hubspot_trigger import HubSpotTriggerNode
from apps.api.app.node_system.nodes.huggingface.huggingface_node import HuggingFaceNode
from apps.api.app.node_system.nodes.instantly.instantly_node import InstantlyNode
from apps.api.app.node_system.nodes.intercom.intercom_node import IntercomNode
from apps.api.app.node_system.nodes.intercom.intercom_trigger import IntercomTriggerNode
from apps.api.app.node_system.nodes.jira.jira_node import JiraNode
from apps.api.app.node_system.nodes.jira.jira_trigger import JiraTriggerNode
from apps.api.app.node_system.nodes.klaviyo.klaviyo_node import KlaviyoNode
from apps.api.app.node_system.nodes.linear.linear_node import LinearNode
from apps.api.app.node_system.nodes.linear.linear_trigger import LinearTriggerNode
from apps.api.app.node_system.nodes.linkedin.linkedin_node import LinkedInNode
from apps.api.app.node_system.nodes.logic.code.code_node import CodeNode
from apps.api.app.node_system.nodes.logic.do_while.do_while import DoWhileNode
from apps.api.app.node_system.nodes.logic.for_loop.for_loop import ForLoopNode
from apps.api.app.node_system.nodes.logic.foreach.foreach import ForEachNode
from apps.api.app.node_system.nodes.logic.human_input.human_input import HumanInputNode
from apps.api.app.node_system.nodes.logic.loop.loop_node import LoopNode
from apps.api.app.node_system.nodes.logic.sub_workflow.sub_workflow_node import SubWorkflowNode
from apps.api.app.node_system.nodes.logic.while_loop.while_loop import WhileLoopNode
from apps.api.app.node_system.nodes.loops.loops_node import LoopsNode
from apps.api.app.node_system.nodes.mailchimp.mailchimp_node import MailchimpNode
from apps.api.app.node_system.nodes.mailerlite.mailerlite_node import MailerLiteNode
from apps.api.app.node_system.nodes.mailgun.mailgun_node import MailgunNode
from apps.api.app.node_system.nodes.messagebird.messagebird_node import MessageBirdNode
from apps.api.app.node_system.nodes.meta.facebook_action import FacebookActionNode
from apps.api.app.node_system.nodes.meta.facebook_trigger import FacebookTriggerNode
from apps.api.app.node_system.nodes.meta.instagram_action import InstagramActionNode
from apps.api.app.node_system.nodes.meta.instagram_trigger import InstagramTriggerNode
from apps.api.app.node_system.nodes.meta.lead_action import LeadActionNode
from apps.api.app.node_system.nodes.meta.lead_trigger import LeadTriggerNode
from apps.api.app.node_system.nodes.meta.whatsapp_action import WhatsAppActionNode
from apps.api.app.node_system.nodes.meta.whatsapp_trigger import WhatsAppTriggerNode
from apps.api.app.node_system.nodes.microsoft_excel.microsoft_excel_node import MicrosoftExcelNode
from apps.api.app.node_system.nodes.microsoft_planner.microsoft_planner_node import (
    MicrosoftPlannerNode,
)
from apps.api.app.node_system.nodes.microsoft_teams.microsoft_teams_node import MicrosoftTeamsNode
from apps.api.app.node_system.nodes.microsoft_teams.microsoft_teams_webhook import (
    MicrosoftTeamsWebhookTriggerNode,
)
from apps.api.app.node_system.nodes.mixpanel.mixpanel_node import MixpanelNode
from apps.api.app.node_system.nodes.monday.monday_node import MondayNode
from apps.api.app.node_system.nodes.newsapi.newsapi_node import NewsAPINode
from apps.api.app.node_system.nodes.notion.notion_node import NotionNode
from apps.api.app.node_system.nodes.notion.notion_trigger import NotionTriggerNode
from apps.api.app.node_system.nodes.onedrive.onedrive_node import OneDriveNode
from apps.api.app.node_system.nodes.openalex.openalex_node import OpenAlexNode
from apps.api.app.node_system.nodes.outlook.outlook_node import OutlookNode
from apps.api.app.node_system.nodes.outlook.outlook_trigger import OutlookMailTriggerNode
from apps.api.app.node_system.nodes.pagerduty.pagerduty_trigger import PagerDutyTriggerNode
from apps.api.app.node_system.nodes.pinecone.pinecone_node import PineconeNode
from apps.api.app.node_system.nodes.pipedrive.pipedrive_node import PipedriveNode
from apps.api.app.node_system.nodes.plivo.plivo_node import PlivoNode
from apps.api.app.node_system.nodes.posthog.posthog_node import PostHogNode
from apps.api.app.node_system.nodes.postmark.postmark_node import PostmarkNode
from apps.api.app.node_system.nodes.qdrant.qdrant_node import QdrantNode
from apps.api.app.node_system.nodes.resend.resend_node import ResendNode
from apps.api.app.node_system.nodes.salesforce.salesforce_node import SalesforceNode
from apps.api.app.node_system.nodes.sendblue.sendblue_node import SendblueNode
from apps.api.app.node_system.nodes.sendgrid.sendgrid_node import SendGridNode
from apps.api.app.node_system.nodes.sentry.sentry_node import SentryNode
from apps.api.app.node_system.nodes.serper.serper_node import SerperNode
from apps.api.app.node_system.nodes.sharepoint.sharepoint_node import SharePointNode
from apps.api.app.node_system.nodes.shopify.shopify_node import ShopifyNode
from apps.api.app.node_system.nodes.slack.slack_node import SlackNode
from apps.api.app.node_system.nodes.slack.slack_trigger import SlackTriggerNode
from apps.api.app.node_system.nodes.square.square_node import SquareNode
from apps.api.app.node_system.nodes.stripe.stripe_node import StripeNode
from apps.api.app.node_system.nodes.supabase.supabase_node import SupabaseNode
from apps.api.app.node_system.nodes.tavily.tavily_node import TavilyNode
from apps.api.app.node_system.nodes.telegram.telegram_node import TelegramNode
from apps.api.app.node_system.nodes.telegram.telegram_trigger import TelegramTriggerNode
from apps.api.app.node_system.nodes.tinybird.tinybird_node import TinybirdNode
from apps.api.app.node_system.nodes.trello.trello_node import TrelloNode
from apps.api.app.node_system.nodes.trello.trello_trigger import TrelloTriggerNode
from apps.api.app.node_system.nodes.twilio.twilio_node import TwilioNode
from apps.api.app.node_system.nodes.twilio.twilio_webhook import TwilioWebhookTriggerNode
from apps.api.app.node_system.nodes.typeform.typeform_node import TypeformNode
from apps.api.app.node_system.nodes.upstash_redis.upstash_redis_node import UpstashRedisNode
from apps.api.app.node_system.nodes.vercel.vercel_node import VercelNode
from apps.api.app.node_system.nodes.webflow.webflow_webhook import WebflowWebhookTriggerNode
from apps.api.app.node_system.nodes.wikipedia.wikipedia_node import WikipediaNode
from apps.api.app.node_system.nodes.zendesk.zendesk_node import ZendeskNode
from apps.api.app.node_system.nodes.zendesk.zendesk_trigger import ZendeskTriggerNode
from apps.api.app.node_system.nodes.zoom.zoom_node import ZoomNode


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
node_registry.register(ExaNode)
node_registry.register(TavilyNode)
node_registry.register(SerperNode)
node_registry.register(BrandfetchNode)
node_registry.register(HuggingFaceNode)
node_registry.register(ResendNode)
node_registry.register(SendGridNode)
node_registry.register(PostmarkNode)
node_registry.register(LoopsNode)
node_registry.register(InstantlyNode)
node_registry.register(WikipediaNode)
node_registry.register(OpenAlexNode)
node_registry.register(DuckDuckGoNode)
node_registry.register(HackerNewsNode)
node_registry.register(NewsAPINode)
node_registry.register(SentryNode)
node_registry.register(PostHogNode)
node_registry.register(DubNode)
node_registry.register(VercelNode)
node_registry.register(CloudflareNode)
node_registry.register(SupabaseNode)
node_registry.register(UpstashRedisNode)
node_registry.register(PineconeNode)
node_registry.register(QdrantNode)
node_registry.register(TinybirdNode)
node_registry.register(TwilioNode)
node_registry.register(MailgunNode)
node_registry.register(SendblueNode)
node_registry.register(MessageBirdNode)
node_registry.register(PlivoNode)
node_registry.register(PipedriveNode)
node_registry.register(AttioNode)
node_registry.register(MixpanelNode)
node_registry.register(MondayNode)
node_registry.register(IntercomNode)
node_registry.register(TypeformNode)
node_registry.register(ShopifyNode)
node_registry.register(ApifyNode)
node_registry.register(AlgoliaNode)
node_registry.register(SquareNode)
# Phase 2.1 — Microsoft 365 family (shared microsoft_oauth credential).
node_registry.register(OutlookNode)
node_registry.register(MicrosoftTeamsNode)
node_registry.register(OneDriveNode)
node_registry.register(SharePointNode)
node_registry.register(MicrosoftExcelNode)
# Phase 2.2 — CRM / meetings OAuth majors.
node_registry.register(AsanaNode)
node_registry.register(CalendlyNode)
node_registry.register(ZoomNode)
node_registry.register(BoxNode)
# Phase 2.3 — AWS family (SigV4).
node_registry.register(AWSS3Node)
node_registry.register(AWSSESNode)
node_registry.register(AWSSQSNode)
node_registry.register(AWSSecretsManagerNode)
node_registry.register(AWSAthenaNode)
# Phase 2.6 — AWS completion (RDS + IAM + STS + CloudWatch Logs +
# CloudFormation) + Microsoft Planner.
node_registry.register(AWSRDSNode)
node_registry.register(AWSIAMNode)
node_registry.register(AWSSTSNode)
node_registry.register(AWSCloudWatchLogsNode)
node_registry.register(AWSCloudFormationNode)
node_registry.register(MicrosoftPlannerNode)
# Phase 2.7 — CRM completion (trello, zendesk, calcom).
node_registry.register(TrelloNode)
node_registry.register(ZendeskNode)
node_registry.register(CalcomNode)
# Phase 3.1 — dev/CRM polling triggers.
node_registry.register(GitLabTriggerNode)
node_registry.register(JiraTriggerNode)
node_registry.register(HubSpotTriggerNode)
node_registry.register(AsanaTriggerNode)
node_registry.register(PagerDutyTriggerNode)
# Phase 3.2 — task/support polling triggers.
node_registry.register(TrelloTriggerNode)
node_registry.register(CalendlyTriggerNode)
node_registry.register(CalcomTriggerNode)
node_registry.register(NotionTriggerNode)
node_registry.register(IntercomTriggerNode)
# Phase 3.3 — support/notif polling triggers.
node_registry.register(ZendeskTriggerNode)
node_registry.register(OutlookMailTriggerNode)
node_registry.register(LinearTriggerNode)
node_registry.register(TelegramTriggerNode)
# Phase 3.4 — webhook triggers.
node_registry.register(AzureDevOpsWebhookTriggerNode)
node_registry.register(TwilioWebhookTriggerNode)
node_registry.register(MicrosoftTeamsWebhookTriggerNode)
node_registry.register(WebflowWebhookTriggerNode)
node_registry.register(GongWebhookTriggerNode)
node_registry.register(FathomWebhookTriggerNode)
node_registry.register(FirefliesWebhookTriggerNode)
# Phase 2.4 — meetings + docs.
node_registry.register(DropboxNode)
node_registry.register(DocuSignNode)
node_registry.register(FirefliesNode)
node_registry.register(GongNode)
node_registry.register(FathomNode)
# Phase 2.5 — social + marketing.
node_registry.register(LinkedInNode)
node_registry.register(MailchimpNode)
node_registry.register(KlaviyoNode)
node_registry.register(CustomerIONode)
node_registry.register(MailerLiteNode)
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

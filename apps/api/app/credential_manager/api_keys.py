from pydantic import BaseModel


class CredentialField(BaseModel):
    id: str
    label: str
    type: str
    placeholder: str


class APIKeyProvider:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        hint: str,
        fields: list[CredentialField],
        # Brand identity — frontend renders the theSVG mark by slug and
        # uses `color` for the tile background.
        icon_slug: str | None = None,
        color: str | None = None,
        ai_provider_id: str | None = None,
        default_model: str | None = None,
        supports_tools: bool = False,
        supports_response_format: bool = False,
        ai_api_type: str | None = None,
        chat_completions_url: str | None = None,
        models_url: str | None = None,
    ):
        self.id = id
        self.name = name
        self.type = "api_key"
        self.description = description
        self.icon_slug = icon_slug
        self.color = color
        self.hint = hint
        self.fields = fields
        self.ai_provider_id = ai_provider_id
        self.default_model = default_model
        self.supports_tools = supports_tools
        self.supports_response_format = supports_response_format
        self.ai_api_type = ai_api_type
        self.chat_completions_url = chat_completions_url
        self.models_url = models_url


PROVIDERS = {
    "browser_use": APIKeyProvider(
        id="browser_use_api_key",
        name="Browser Use",
        icon_slug=None,
        color="#ffffff",
        description="Browser Use — AI-powered browser automation via browser-use.com",
        hint="bu-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="bu-...")
        ],
    ),
    "firecrawl": APIKeyProvider(
        id="firecrawl_api_key",
        name="Firecrawl",
        icon_slug="firecrawl",
        color="#1c1c1c",
        description="Firecrawl — scrape, crawl, map, and search the web into LLM-ready markdown.",
        hint="fc-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="fc-...")
        ],
    ),
    "mailchimp": APIKeyProvider(
        id="mailchimp_api_key",
        name="Mailchimp",
        icon_slug="mailchimp",
        color="#1c1c1c",
        description="Mailchimp — audiences, campaigns, transactional.",
        hint="API Key (ends in -us14) + data-center suffix from the key",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="abc123-us14",
            ),
            CredentialField(
                id="dc",
                label="Data Center",
                type="string",
                placeholder="us14 (the suffix after the dash in your API key)",
            ),
        ],
    ),
    "klaviyo": APIKeyProvider(
        id="klaviyo_api_key",
        name="Klaviyo",
        icon_slug="klaviyo",
        color="#1c1c1c",
        description="Klaviyo — email + SMS marketing, profiles, events.",
        hint="Private API Key (pk_...)",
        fields=[
            CredentialField(
                id="api_key", label="Private API Key", type="password", placeholder="pk_..."
            )
        ],
    ),
    "customer_io": APIKeyProvider(
        id="customer_io_api_key",
        name="Customer.io",
        icon_slug="customer-io",
        color="#1c1c1c",
        description="Customer.io — behavioral messaging + broadcasts.",
        hint="Track site ID + track API key",
        fields=[
            CredentialField(
                id="site_id",
                label="Site ID",
                type="string",
                placeholder="Site ID",
            ),
            CredentialField(
                id="api_key",
                label="Track API Key",
                type="password",
                placeholder="Track API Key",
            ),
        ],
    ),
    "mailerlite": APIKeyProvider(
        id="mailerlite_api_key",
        name="MailerLite",
        icon_slug="mailerlite",
        color="#1c1c1c",
        description="MailerLite — subscribers, campaigns, automations.",
        hint="API Token",
        fields=[
            CredentialField(id="api_key", label="API Token", type="password", placeholder="Token")
        ],
    ),
    "gitlab": APIKeyProvider(
        id="gitlab_api_key",
        name="GitLab",
        icon_slug="gitlab",
        color="#1c1c1c",
        description="GitLab — projects, issues, MRs, pipelines.",
        hint="Personal Access Token",
        fields=[
            CredentialField(
                id="api_key", label="Access Token", type="password", placeholder="glpat-..."
            ),
            CredentialField(
                id="base_url",
                label="Base URL (self-hosted; leave blank for gitlab.com)",
                type="string",
                placeholder="https://gitlab.example.com",
            ),
        ],
    ),
    "pagerduty": APIKeyProvider(
        id="pagerduty_api_key",
        name="PagerDuty",
        icon_slug="pagerduty",
        color="#1c1c1c",
        description="PagerDuty — incidents, services, on-call.",
        hint="REST API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "trello": APIKeyProvider(
        id="trello_api_key",
        name="Trello",
        icon_slug="trello",
        color="#1c1c1c",
        description="Trello — boards, lists, cards. Uses API key + user token.",
        hint="API key (public) + Token (private per-user)",
        fields=[
            CredentialField(
                id="app_key",
                label="API Key",
                type="string",
                placeholder="from trello.com/app-key",
            ),
            CredentialField(
                id="api_key",
                label="User Token",
                type="password",
                placeholder="Manual token or OAuth1 accessToken",
            ),
        ],
    ),
    "zendesk": APIKeyProvider(
        id="zendesk_api_key",
        name="Zendesk",
        icon_slug="zendesk",
        color="#1c1c1c",
        description="Zendesk — tickets, users, orgs. Uses email/token Basic auth + per-subdomain URL.",
        hint="Subdomain + email + API token",
        fields=[
            CredentialField(
                id="subdomain",
                label="Subdomain",
                type="string",
                placeholder="mycompany (from mycompany.zendesk.com)",
            ),
            CredentialField(
                id="email",
                label="Agent Email",
                type="string",
                placeholder="you@company.com",
            ),
            CredentialField(
                id="api_key",
                label="API Token",
                type="password",
                placeholder="API Token",
            ),
        ],
    ),
    "calcom": APIKeyProvider(
        id="calcom_api_key",
        name="Cal.com",
        icon_slug="calcom",
        color="#1c1c1c",
        description="Cal.com — bookings, event types, availability.",
        hint="cal_live_... (Cal.com API key)",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="cal_live_..."
            )
        ],
    ),
    "fireflies": APIKeyProvider(
        id="fireflies_api_key",
        name="Fireflies",
        icon_slug="fireflies",
        color="#1c1c1c",
        description="Fireflies.ai — meeting transcripts + summaries + search (GraphQL).",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "gong": APIKeyProvider(
        id="gong_api_key",
        name="Gong",
        icon_slug="gong",
        color="#1c1c1c",
        description="Gong.io — call recordings, transcripts, deal insights.",
        hint="Access Key + Access Key Secret",
        fields=[
            CredentialField(
                id="access_key",
                label="Access Key",
                type="string",
                placeholder="Access Key",
            ),
            CredentialField(
                id="access_key_secret",
                label="Access Key Secret",
                type="password",
                placeholder="Secret",
            ),
        ],
    ),
    "fathom": APIKeyProvider(
        id="fathom_api_key",
        name="Fathom",
        icon_slug="fathom",
        color="#1c1c1c",
        description="Fathom.video — meeting recordings, transcripts, action items.",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "aws": APIKeyProvider(
        id="aws_credentials",
        name="AWS",
        icon_slug="aws",
        color="#1c1c1c",
        description=(
            "AWS access key + secret access key. Signs SigV4 requests "
            "for S3, SES, SQS, Secrets Manager, Athena, and other AWS APIs."
        ),
        hint="Access Key ID + Secret Access Key + Region",
        fields=[
            CredentialField(
                id="access_key_id",
                label="Access Key ID",
                type="string",
                placeholder="AKIA...",
            ),
            CredentialField(
                id="secret_access_key",
                label="Secret Access Key",
                type="password",
                placeholder="secret",
            ),
            CredentialField(
                id="region",
                label="Default Region",
                type="string",
                placeholder="us-east-1",
            ),
            CredentialField(
                id="session_token",
                label="Session Token (optional, STS)",
                type="password",
                placeholder="STS token",
            ),
        ],
    ),
    "typeform": APIKeyProvider(
        id="typeform_api_key",
        name="Typeform",
        icon_slug="typeform",
        color="#1c1c1c",
        description="Typeform — forms, responses, webhooks.",
        hint="Personal Access Token",
        fields=[
            CredentialField(
                id="api_key", label="Access Token", type="password", placeholder="Token"
            )
        ],
    ),
    "shopify": APIKeyProvider(
        id="shopify_api_key",
        name="Shopify",
        icon_slug="shopify",
        color="#1c1c1c",
        description="Shopify Admin — orders, products, customers.",
        hint="Admin API access token + store domain",
        fields=[
            CredentialField(
                id="store_domain",
                label="Store Domain",
                type="string",
                placeholder="your-store (without .myshopify.com)",
            ),
            CredentialField(
                id="api_key", label="Access Token", type="password", placeholder="shpat_..."
            ),
        ],
    ),
    "apify": APIKeyProvider(
        id="apify_api_key",
        name="Apify",
        icon_slug="apify",
        color="#1c1c1c",
        description="Apify — actors, datasets, key-value stores.",
        hint="Personal API token",
        fields=[
            CredentialField(
                id="api_key", label="API Token", type="password", placeholder="apify_api_..."
            )
        ],
    ),
    "algolia": APIKeyProvider(
        id="algolia_api_key",
        name="Algolia",
        icon_slug="algolia",
        color="#1c1c1c",
        description="Algolia — index, search, manage records.",
        hint="Application ID + Admin / Search API key",
        fields=[
            CredentialField(
                id="app_id",
                label="Application ID",
                type="string",
                placeholder="ABC123",
            ),
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key"),
        ],
    ),
    "square": APIKeyProvider(
        id="square_api_key",
        name="Square",
        icon_slug="square",
        color="#1c1c1c",
        description="Square Connect — payments, orders, customers, catalog.",
        hint="Access Token",
        fields=[
            CredentialField(
                id="api_key", label="Access Token", type="password", placeholder="EAAA..."
            )
        ],
    ),
    "pipedrive": APIKeyProvider(
        id="pipedrive_api_key",
        name="Pipedrive",
        icon_slug="pipedrive",
        color="#1c1c1c",
        description="Pipedrive CRM — deals, persons, organizations.",
        hint="API token + company domain",
        fields=[
            CredentialField(
                id="company_domain",
                label="Company Domain",
                type="string",
                placeholder="your-team",
            ),
            CredentialField(id="api_key", label="API Token", type="password", placeholder="Token"),
        ],
    ),
    "attio": APIKeyProvider(
        id="attio_api_key",
        name="Attio",
        icon_slug="attio",
        color="#1c1c1c",
        description="Attio CRM — flexible-schema records, lists, and objects.",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "mixpanel": APIKeyProvider(
        id="mixpanel_api_key",
        name="Mixpanel",
        icon_slug="mixpanel",
        color="#1c1c1c",
        description="Mixpanel — event tracking + engagement queries.",
        hint="Service account username + secret (project token for ingestion)",
        fields=[
            CredentialField(
                id="username",
                label="Service Account Username",
                type="string",
                placeholder="serviceaccount.user",
            ),
            CredentialField(
                id="api_secret",
                label="Service Account Secret",
                type="password",
                placeholder="Secret",
            ),
        ],
    ),
    "monday": APIKeyProvider(
        id="monday_api_key",
        name="Monday.com",
        icon_slug="monday",
        color="#1c1c1c",
        description="Monday.com — boards, items, updates via GraphQL.",
        hint="API token (Profile → Admin → API)",
        fields=[
            CredentialField(id="api_key", label="API Token", type="password", placeholder="Token")
        ],
    ),
    "intercom": APIKeyProvider(
        id="intercom_api_key",
        name="Intercom",
        icon_slug="intercom",
        color="#1c1c1c",
        description="Intercom — contacts, conversations, messages.",
        hint="Access token (Developer Hub → Authentication)",
        fields=[
            CredentialField(
                id="api_key", label="Access Token", type="password", placeholder="Token"
            )
        ],
    ),
    "twilio": APIKeyProvider(
        id="twilio_api_key",
        name="Twilio",
        icon_slug="twilio",
        color="#1c1c1c",
        description="Twilio — SMS, WhatsApp, voice. Auth Token + Account SID.",
        hint="Account SID + Auth Token",
        fields=[
            CredentialField(
                id="account_sid",
                label="Account SID",
                type="string",
                placeholder="AC...",
            ),
            CredentialField(
                id="auth_token",
                label="Auth Token",
                type="password",
                placeholder="Auth Token",
            ),
        ],
    ),
    "mailgun": APIKeyProvider(
        id="mailgun_api_key",
        name="Mailgun",
        icon_slug="mailgun",
        color="#1c1c1c",
        description="Mailgun — transactional + marketing email.",
        hint="key-... (private API key)",
        fields=[
            CredentialField(
                id="api_key", label="Private API Key", type="password", placeholder="key-..."
            )
        ],
    ),
    "sendblue": APIKeyProvider(
        id="sendblue_api_key",
        name="Sendblue",
        icon_slug="sendblue",
        color="#1c1c1c",
        description="Sendblue — iMessage + SMS fallback messaging.",
        hint="API Key ID + Secret",
        fields=[
            CredentialField(
                id="api_key_id",
                label="API Key ID",
                type="string",
                placeholder="key id",
            ),
            CredentialField(
                id="api_secret_key",
                label="API Secret Key",
                type="password",
                placeholder="secret key",
            ),
        ],
    ),
    "messagebird": APIKeyProvider(
        id="messagebird_api_key",
        name="MessageBird",
        icon_slug="messagebird",
        color="#1c1c1c",
        description="MessageBird — SMS, voice, verification.",
        hint="Access Key",
        fields=[
            CredentialField(
                id="api_key", label="Access Key", type="password", placeholder="Access Key"
            )
        ],
    ),
    "plivo": APIKeyProvider(
        id="plivo_api_key",
        name="Plivo",
        icon_slug="plivo",
        color="#1c1c1c",
        description="Plivo — SMS and voice. Auth ID + Auth Token.",
        hint="Auth ID + Auth Token",
        fields=[
            CredentialField(id="auth_id", label="Auth ID", type="string", placeholder="MA..."),
            CredentialField(
                id="auth_token", label="Auth Token", type="password", placeholder="Auth Token"
            ),
        ],
    ),
    "supabase": APIKeyProvider(
        id="supabase_api_key",
        name="Supabase",
        icon_slug="supabase",
        color="#1c1c1c",
        description="Supabase — read/write Postgres tables via PostgREST.",
        hint="Service role or anon key + project URL",
        fields=[
            CredentialField(
                id="project_url",
                label="Project URL",
                type="string",
                placeholder="https://abc.supabase.co",
            ),
            CredentialField(id="api_key", label="API Key", type="password", placeholder="eyJ..."),
        ],
    ),
    "upstash_redis": APIKeyProvider(
        id="upstash_redis_api_key",
        name="Upstash Redis",
        icon_slug="upstash",
        color="#1c1c1c",
        description="Upstash Redis — REST-driven Redis commands.",
        hint="REST URL + REST token",
        fields=[
            CredentialField(
                id="rest_url",
                label="REST URL",
                type="string",
                placeholder="https://abc-12345.upstash.io",
            ),
            CredentialField(id="api_key", label="REST Token", type="password", placeholder="Token"),
        ],
    ),
    "pinecone": APIKeyProvider(
        id="pinecone_api_key",
        name="Pinecone",
        icon_slug="pinecone",
        color="#1c1c1c",
        description="Pinecone — vector database control + data plane.",
        hint="API key + per-index host",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key"),
            CredentialField(
                id="index_host",
                label="Index Host (optional, data-plane ops)",
                type="string",
                placeholder="abc-123456.svc.us-east-1.aws.pinecone.io",
            ),
        ],
    ),
    "qdrant": APIKeyProvider(
        id="qdrant_api_key",
        name="Qdrant",
        icon_slug="qdrant",
        color="#1c1c1c",
        description="Qdrant — vector database (cloud or self-hosted).",
        hint="Cluster URL + API key",
        fields=[
            CredentialField(
                id="cluster_url",
                label="Cluster URL",
                type="string",
                placeholder="https://abc.us-east.aws.cloud.qdrant.io:6333",
            ),
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key"),
        ],
    ),
    "tinybird": APIKeyProvider(
        id="tinybird_api_key",
        name="Tinybird",
        icon_slug="tinybird",
        color="#1c1c1c",
        description="Tinybird — managed ClickHouse for product analytics.",
        hint="Workspace admin or pipe token",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="p.eyJ...")
        ],
    ),
    "sentry": APIKeyProvider(
        id="sentry_api_key",
        name="Sentry",
        icon_slug="sentry",
        color="#1c1c1c",
        description="Sentry — error tracking + release management.",
        hint="Auth Token",
        fields=[
            CredentialField(
                id="api_key", label="Auth Token", type="password", placeholder="sntrys_..."
            )
        ],
    ),
    "posthog": APIKeyProvider(
        id="posthog_api_key",
        name="PostHog",
        icon_slug="posthog",
        color="#1c1c1c",
        description="PostHog — product analytics + feature flags.",
        hint="phx_...",
        fields=[
            CredentialField(
                id="api_key", label="Personal API Key", type="password", placeholder="phx_..."
            )
        ],
    ),
    "dub": APIKeyProvider(
        id="dub_api_key",
        name="Dub",
        icon_slug="dub",
        color="#1c1c1c",
        description="Dub.co — short links + click analytics.",
        hint="dub_...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="dub_...")
        ],
    ),
    "vercel": APIKeyProvider(
        id="vercel_api_key",
        name="Vercel",
        icon_slug="vercel",
        color="#ffffff",
        description="Vercel — deployments, projects, env vars, domains.",
        hint="Personal Access Token",
        fields=[
            CredentialField(
                id="api_key", label="Access Token", type="password", placeholder="Token"
            )
        ],
    ),
    "cloudflare": APIKeyProvider(
        id="cloudflare_api_key",
        name="Cloudflare",
        icon_slug="cloudflare",
        color="#1c1c1c",
        description="Cloudflare — zones, DNS, cache, workers via scoped API token.",
        hint="API Token (scoped, not the global key)",
        fields=[
            CredentialField(id="api_key", label="API Token", type="password", placeholder="Token")
        ],
    ),
    "newsapi": APIKeyProvider(
        id="newsapi_api_key",
        name="NewsAPI",
        icon_slug="newsapi",
        color="#1c1c1c",
        description="NewsAPI.org — search 80k+ news sources.",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "resend": APIKeyProvider(
        id="resend_api_key",
        name="Resend",
        icon_slug="resend",
        color="#1c1c1c",
        description="Resend — transactional email API.",
        hint="re_...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="re_...")
        ],
    ),
    "sendgrid": APIKeyProvider(
        id="sendgrid_api_key",
        name="SendGrid",
        icon_slug="sendgrid",
        color="#1c1c1c",
        description="SendGrid — transactional + marketing email.",
        hint="SG....",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="SG....")
        ],
    ),
    "postmark": APIKeyProvider(
        id="postmark_api_key",
        name="Postmark",
        icon_slug="postmark",
        color="#1c1c1c",
        description="Postmark — fast transactional email.",
        hint="Server Token (one per Postmark server)",
        fields=[
            CredentialField(
                id="api_key", label="Server Token", type="password", placeholder="Server Token"
            )
        ],
    ),
    "loops": APIKeyProvider(
        id="loops_api_key",
        name="Loops",
        icon_slug="loops",
        color="#1c1c1c",
        description="Loops.so — product email + audience automation.",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "lemlist": APIKeyProvider(
        id="lemlist_api_key",
        name="Lemlist",
        icon_slug="lemlist",
        color="#1c1c1c",
        description="Lemlist — outbound email campaigns, leads, activities.",
        hint="API key from Lemlist Settings → API",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="Lemlist API key",
            ),
        ],
    ),
    "emailbison": APIKeyProvider(
        id="emailbison_api_key",
        name="Emailbison",
        icon_slug="emailbison",
        color="#1c1c1c",
        description="Emailbison — outbound-email campaigns, leads, workspaces.",
        hint="API key from Emailbison workspace settings",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="Emailbison API key",
            ),
        ],
    ),
    "instantly": APIKeyProvider(
        id="instantly_api_key",
        name="Instantly",
        icon_slug="instantly",
        color="#1c1c1c",
        description="Instantly.ai — cold-email outreach + lead management.",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "exa": APIKeyProvider(
        id="exa_api_key",
        name="Exa",
        icon_slug="exa",
        color="#1c1c1c",
        description="Exa — neural web search + content extraction.",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "tavily": APIKeyProvider(
        id="tavily_api_key",
        name="Tavily",
        icon_slug="tavily",
        color="#1c1c1c",
        description="Tavily — LLM-grounded search + URL extraction.",
        hint="tvly-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="tvly-...")
        ],
    ),
    "serper": APIKeyProvider(
        id="serper_api_key",
        name="Serper",
        icon_slug="serper",
        color="#1c1c1c",
        description="Serper — Google search results via google.serper.dev.",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "brandfetch": APIKeyProvider(
        id="brandfetch_api_key",
        name="Brandfetch",
        icon_slug="brandfetch",
        color="#1c1c1c",
        description="Brandfetch — pull brand identity assets by domain.",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "huggingface": APIKeyProvider(
        id="huggingface_api_key",
        name="HuggingFace",
        icon_slug="huggingface",
        color="#ffffff",
        description="HuggingFace Hosted Inference — run any model from the Hub.",
        hint="hf_...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="hf_...")
        ],
    ),
    "airtable": APIKeyProvider(
        id="airtable_api_key",
        name="Airtable",
        icon_slug="airtable",
        color="#1c1c1c",
        description="Airtable — database and spreadsheet automation",
        hint="pat...",
        fields=[
            CredentialField(
                id="api_key", label="Personal Access Token", type="password", placeholder="pat..."
            )
        ],
    ),
    "stripe": APIKeyProvider(
        id="stripe_api_key",
        name="Stripe",
        icon_slug="stripe",
        color="#ffffff",
        description="Stripe — payments and billing automation",
        hint="sk_live_... or sk_test_...",
        fields=[
            CredentialField(
                id="api_key", label="Secret Key", type="password", placeholder="sk_live_..."
            )
        ],
    ),
    "hubspot": APIKeyProvider(
        id="hubspot_api_key",
        name="HubSpot",
        icon_slug="hubspot",
        color="#1c1c1c",
        description="HubSpot — CRM contacts, deals, and companies",
        hint="Private App Token",
        fields=[
            CredentialField(
                id="api_key", label="Private App Token", type="password", placeholder="pat-na1-..."
            )
        ],
    ),
    "linear": APIKeyProvider(
        id="linear_api_key",
        name="Linear",
        icon_slug="linear",
        color="#1c1c1c",
        description="Linear project management — create and manage issues",
        hint="lin_api_...",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="lin_api_..."
            )
        ],
    ),
    "perplexity": APIKeyProvider(
        id="perplexity_api_key",
        name="Perplexity",
        icon_slug="perplexity",
        color="#1c1c1c",
        description="Perplexity Sonar — web search + LLM with live internet access",
        hint="pplx-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="pplx-...")
        ],
    ),
    "elevenlabs": APIKeyProvider(
        id="elevenlabs_api_key",
        name="ElevenLabs",
        icon_slug="elevenlabs",
        color="#ffffff",
        description="High-quality text-to-speech with voice cloning",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "notion": APIKeyProvider(
        id="notion_api_key",
        name="Notion",
        icon_slug="notion",
        color="#ffffff",
        description="Connect to Notion using an Internal Integration Token",
        hint="secret_...",
        fields=[
            CredentialField(
                id="api_key",
                label="Integration Token",
                type="password",
                placeholder="secret_...",
            )
        ],
    ),
    "openai": APIKeyProvider(
        id="openai_api_key",
        name="OpenAI",
        icon_slug="openai",
        color="#ffffff",
        description="Use your OpenAI API key for AI nodes",
        hint="sk-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="sk-...")
        ],
        ai_provider_id="openai",
        default_model="gpt-4o-mini",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="openai_compatible",
        chat_completions_url="https://api.openai.com/v1/chat/completions",
        models_url="https://api.openai.com/v1/models",
    ),
    "anthropic": APIKeyProvider(
        id="anthropic_api_key",
        name="Anthropic",
        icon_slug="anthropic",
        color="#ffffff",
        description="Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku",
        hint="sk-ant-...",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="sk-ant-..."
            )
        ],
        ai_provider_id="anthropic",
        default_model="claude-3-5-sonnet-latest",
        supports_tools=True,
        supports_response_format=False,
        ai_api_type="anthropic",
        chat_completions_url="https://api.anthropic.com/v1/messages",
        models_url="https://api.anthropic.com/v1/models",
    ),
    "google": APIKeyProvider(
        id="google_api_key",
        name="Google Gemini",
        icon_slug="google-gemini",
        color="#1c1c1c",
        description="Gemini 1.5 Pro, Gemini 1.5 Flash",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
        ai_provider_id="google",
        default_model="gemini-1.5-flash",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="google",
        chat_completions_url="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        models_url="https://generativelanguage.googleapis.com/v1beta/models",
    ),
    "groq": APIKeyProvider(
        id="groq_api_key",
        name="Groq",
        icon_slug="groq",
        color="#1c1c1c",
        description="Llama 3, Mixtral, Gemma (Ultra-fast inference)",
        hint="gsk-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="gsk-...")
        ],
        ai_provider_id="groq",
        default_model="llama-3.1-8b-instant",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="openai_compatible",
        chat_completions_url="https://api.groq.com/openai/v1/chat/completions",
        models_url="https://api.groq.com/openai/v1/models",
    ),
    "openrouter": APIKeyProvider(
        id="openrouter_api_key",
        name="OpenRouter",
        icon_slug="openrouter",
        color="#1c1c1c",
        description="Access many model providers through the OpenRouter API",
        hint="sk-or-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="sk-or-...")
        ],
        ai_provider_id="openrouter",
        default_model="openai/gpt-4o-mini",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="openai_compatible",
        chat_completions_url="https://openrouter.ai/api/v1/chat/completions",
        models_url="https://openrouter.ai/api/v1/models",
    ),
    "deepseek": APIKeyProvider(
        id="deepseek_api_key",
        name="DeepSeek",
        icon_slug="deepseek",
        color="#ffffff",
        description="DeepSeek chat and reasoning models",
        hint="sk-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="sk-...")
        ],
        ai_provider_id="deepseek",
        default_model="deepseek-chat",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="openai_compatible",
        chat_completions_url="https://api.deepseek.com/chat/completions",
        models_url="https://api.deepseek.com/models",
    ),
    "mistral": APIKeyProvider(
        id="mistral_api_key",
        name="Mistral AI",
        icon_slug="mistral",
        color="#ffffff",
        description="Mistral chat and code models",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
        ai_provider_id="mistral",
        default_model="mistral-small-latest",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="openai_compatible",
        chat_completions_url="https://api.mistral.ai/v1/chat/completions",
        models_url="https://api.mistral.ai/v1/models",
    ),
    "xai": APIKeyProvider(
        id="xai_api_key",
        name="xAI",
        icon_slug="xai",
        color="#ffffff",
        description="Grok models from xAI",
        hint="xai-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="xai-...")
        ],
        ai_provider_id="xai",
        default_model="grok-4",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="openai_compatible",
        chat_completions_url="https://api.x.ai/v1/chat/completions",
        models_url="https://api.x.ai/v1/models",
    ),
    "together": APIKeyProvider(
        id="together_api_key",
        name="Together AI",
        icon_slug="together-ai",
        color="#1c1c1c",
        description="Open-source and hosted models through Together AI",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
        ai_provider_id="together",
        default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="openai_compatible",
        chat_completions_url="https://api.together.ai/v1/chat/completions",
        models_url="https://api.together.ai/v1/models",
    ),
    "jira": APIKeyProvider(
        id="jira_api_key",
        name="Jira",
        icon_slug="jira",
        color="#ffffff",
        description="Jira — project management and issue tracking via REST API v3",
        hint="https://yoursite.atlassian.net",
        fields=[
            CredentialField(
                id="email", label="Atlassian Email", type="text", placeholder="you@company.com"
            ),
            CredentialField(
                id="api_key", label="API Token", type="password", placeholder="ATATT3x..."
            ),
            CredentialField(
                id="base_url",
                label="Jira Base URL",
                type="text",
                placeholder="https://yoursite.atlassian.net",
            ),
        ],
    ),
    "ashby": APIKeyProvider(
        id="ashby_api_key",
        name="Ashby",
        icon_slug="ashby",
        color="#1c1c1c",
        description="Ashby ATS — candidates, applications, jobs via POST-based JSON API.",
        hint="API key from Admin → API keys",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="ashby_v1_...",
            ),
        ],
    ),
    "greenhouse": APIKeyProvider(
        id="greenhouse_api_key",
        name="Greenhouse",
        icon_slug="greenhouse",
        color="#1c1c1c",
        description="Greenhouse ATS — jobs, candidates, applications via Harvest API v1.",
        hint="Harvest API key (Basic auth as user, no password)",
        fields=[
            CredentialField(
                id="api_key",
                label="Harvest API Key",
                type="password",
                placeholder="Harvest key from Greenhouse settings",
            ),
        ],
    ),
    "grain": APIKeyProvider(
        id="grain_api_key",
        name="Grain",
        icon_slug="grain",
        color="#1c1c1c",
        description="Grain — meeting recorder, highlights, stories via public API v3.",
        hint="Personal Access Token from Grain settings",
        fields=[
            CredentialField(
                id="api_key",
                label="Access Token",
                type="password",
                placeholder="grain_pat_...",
            ),
        ],
    ),
    "servicenow": APIKeyProvider(
        id="servicenow_api_key",
        name="ServiceNow",
        icon_slug="servicenow",
        color="#1c1c1c",
        description="ServiceNow — ITSM tickets, incidents, change requests via Table API.",
        hint="Instance + username + password",
        fields=[
            CredentialField(
                id="instance",
                label="Instance",
                type="string",
                placeholder="mycompany (from mycompany.service-now.com)",
            ),
            CredentialField(
                id="username",
                label="Username",
                type="string",
                placeholder="you@company.com",
            ),
            CredentialField(
                id="api_key",
                label="Password / API Token",
                type="password",
                placeholder="Password (or scoped OAuth token)",
            ),
        ],
    ),
    "confluence": APIKeyProvider(
        id="confluence_api_key",
        name="Confluence",
        icon_slug="confluence",
        color="#ffffff",
        description="Confluence Cloud — pages, spaces, blogs, comments via REST v2",
        hint="https://yoursite.atlassian.net (same site as Jira)",
        fields=[
            CredentialField(
                id="email",
                label="Atlassian Email",
                type="text",
                placeholder="you@company.com",
            ),
            CredentialField(
                id="api_key",
                label="API Token",
                type="password",
                placeholder="ATATT3x...",
            ),
            CredentialField(
                id="base_url",
                label="Confluence Base URL",
                type="text",
                placeholder="https://yoursite.atlassian.net",
            ),
        ],
    ),
    "salesforce": APIKeyProvider(
        id="salesforce_api_key",
        name="Salesforce",
        icon_slug="salesforce",
        color="#1c1c1c",
        description="Salesforce — CRM records via Connected App access token",
        hint="Access token from Salesforce Connected App",
        fields=[
            CredentialField(
                id="api_key", label="Access Token", type="password", placeholder="00D..."
            ),
            CredentialField(
                id="instance_url",
                label="Instance URL",
                type="text",
                placeholder="https://yourorg.my.salesforce.com",
            ),
        ],
    ),
    "fireworks": APIKeyProvider(
        id="fireworks_api_key",
        name="Fireworks AI",
        icon_slug="fireworks",
        color="#ffffff",
        description="Fast serverless inference for open-weight models",
        hint="fw_...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="fw_...")
        ],
        ai_provider_id="fireworks",
        default_model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        supports_tools=True,
        supports_response_format=True,
        ai_api_type="openai_compatible",
        chat_completions_url="https://api.fireworks.ai/inference/v1/chat/completions",
        models_url="https://api.fireworks.ai/inference/v1/models",
    ),
    "imap": APIKeyProvider(
        id="imap_creds",
        name="IMAP Email",
        icon_slug="mail",
        color="#1c1c1c",
        description="Generic IMAP mailbox — Gmail, Outlook, Yahoo, self-hosted. App-password for Gmail.",
        hint="Host + port + username + password",
        fields=[
            CredentialField(
                id="host",
                label="IMAP Host",
                type="string",
                placeholder="imap.gmail.com",
            ),
            CredentialField(
                id="port",
                label="Port",
                type="string",
                placeholder="993 (IMAPS) or 143 (STARTTLS)",
            ),
            CredentialField(
                id="username",
                label="Username",
                type="string",
                placeholder="you@example.com",
            ),
            CredentialField(
                id="password",
                label="Password / App Password",
                type="password",
                placeholder="App-password (Gmail / Outlook 2FA)",
            ),
            CredentialField(
                id="use_ssl",
                label="Use SSL (true/false)",
                type="string",
                placeholder="true",
            ),
        ],
    ),
    "telegram_bot": APIKeyProvider(
        id="telegram_bot",
        name="Telegram Bot",
        icon_slug="telegram",
        color="#1c1c1c",
        description="Telegram bot token (from @BotFather). Used for send_message + getUpdates polling.",
        hint="Bot token in the form 123456:ABC-DEF...",
        fields=[
            CredentialField(
                id="bot_token",
                label="Bot Token",
                type="password",
                placeholder="123456789:ABCDEF...",
            ),
        ],
    ),
    "apollo": APIKeyProvider(
        id="apollo_api_key",
        name="Apollo.io",
        icon_slug="apollo",
        color="#1c1c1c",
        description="Apollo — B2B contact search + email finder.",
        hint="API key from Apollo Settings → Integrations → API",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Apollo API key"
            ),
        ],
    ),
    "hunter": APIKeyProvider(
        id="hunter_api_key",
        name="Hunter.io",
        icon_slug="hunter",
        color="#1c1c1c",
        description="Hunter — email finder + verifier by domain.",
        hint="API key from Hunter Dashboard → API",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Hunter API key"
            ),
        ],
    ),
    "findymail": APIKeyProvider(
        id="findymail_api_key",
        name="Findymail",
        icon_slug="findymail",
        color="#1c1c1c",
        description="Findymail — verified B2B emails from name / LinkedIn.",
        hint="Bearer token from Findymail settings",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="Findymail API key",
            ),
        ],
    ),
    "dropcontact": APIKeyProvider(
        id="dropcontact_api_key",
        name="Dropcontact",
        icon_slug="dropcontact",
        color="#1c1c1c",
        description="Dropcontact — GDPR-friendly B2B email enrichment.",
        hint="Access token from Dropcontact settings",
        fields=[
            CredentialField(
                id="api_key",
                label="Access Token",
                type="password",
                placeholder="Dropcontact access token",
            ),
        ],
    ),
    "peopledatalabs": APIKeyProvider(
        id="peopledatalabs_api_key",
        name="People Data Labs",
        icon_slug="peopledatalabs",
        color="#1c1c1c",
        description="People Data Labs — person + company enrichment.",
        hint="API key from PDL dashboard",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="PDL API key",
            ),
        ],
    ),
    "clay": APIKeyProvider(
        id="clay_api_key",
        name="Clay",
        icon_slug="clay",
        color="#1c1c1c",
        description="Clay — push rows into a workspace table for enrichment.",
        hint="Workspace webhook URL from a Clay table (paste as api_key)",
        fields=[
            CredentialField(
                id="webhook_url",
                label="Clay Workspace Webhook URL",
                type="string",
                placeholder="https://api.clay.com/v3/sources/webhook/...",
            ),
            CredentialField(
                id="api_key",
                label="Auth Token (optional; some workspaces require)",
                type="password",
                placeholder="Optional",
            ),
        ],
    ),
    "datagma": APIKeyProvider(
        id="datagma_api_key",
        name="Datagma",
        icon_slug="datagma",
        color="#1c1c1c",
        description="Datagma — French B2B contact + company enrichment.",
        hint="API key from Datagma dashboard",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="Datagma API key",
            ),
        ],
    ),
    "enrich": APIKeyProvider(
        id="enrich_api_key",
        name="Enrich.so",
        icon_slug="enrich",
        color="#1c1c1c",
        description="Enrich.so — LinkedIn scraper + email finder.",
        hint="API key from Enrich.so dashboard",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="Enrich.so API key",
            ),
        ],
    ),
    "enrichment": APIKeyProvider(
        id="enrichment_api_key",
        name="Enrichment.io",
        icon_slug="enrichment",
        color="#1c1c1c",
        description="Enrichment — contact + company data-as-a-service.",
        hint="API key from Enrichment.io dashboard",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="Enrichment.io API key",
            ),
        ],
    ),
    "enrow": APIKeyProvider(
        id="enrow_api_key",
        name="Enrow",
        icon_slug="enrow",
        color="#1c1c1c",
        description="Enrow — waterfall B2B email finder + verifier.",
        hint="API key from Enrow dashboard",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="Enrow API key",
            ),
        ],
    ),
    "icypeas": APIKeyProvider(
        id="icypeas_api_key",
        name="Icypeas",
        icon_slug="icypeas",
        color="#1c1c1c",
        description="Icypeas — email finder + LinkedIn enrichment.",
        hint="API key from Icypeas dashboard",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="Icypeas API key",
            ),
        ],
    ),
    "leadmagic": APIKeyProvider(
        id="leadmagic_api_key",
        name="LeadMagic",
        icon_slug="leadmagic",
        color="#1c1c1c",
        description="LeadMagic — email finder + waterfall enrichment.",
        hint="API key from LeadMagic dashboard",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="LeadMagic API key",
            ),
        ],
    ),
    "zerobounce": APIKeyProvider(
        id="zerobounce_api_key",
        name="ZeroBounce",
        icon_slug="zerobounce",
        color="#1c1c1c",
        description="ZeroBounce — email verification + activity data.",
        hint="API key from ZeroBounce dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="ZeroBounce API key"
            ),
        ],
    ),
    "neverbounce": APIKeyProvider(
        id="neverbounce_api_key",
        name="NeverBounce",
        icon_slug="neverbounce",
        color="#1c1c1c",
        description="NeverBounce — real-time email verification.",
        hint="API key from NeverBounce dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="NeverBounce API key"
            ),
        ],
    ),
    "millionverifier": APIKeyProvider(
        id="millionverifier_api_key",
        name="MillionVerifier",
        icon_slug="millionverifier",
        color="#1c1c1c",
        description="MillionVerifier — email + phone verification.",
        hint="API key from MillionVerifier dashboard",
        fields=[
            CredentialField(
                id="api_key",
                label="API Key",
                type="password",
                placeholder="MillionVerifier API key",
            ),
        ],
    ),
    "prospeo": APIKeyProvider(
        id="prospeo_api_key",
        name="Prospeo",
        icon_slug="prospeo",
        color="#1c1c1c",
        description="Prospeo — B2B email finder + verifier.",
        hint="API key from Prospeo dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Prospeo API key"
            ),
        ],
    ),
    "persona": APIKeyProvider(
        id="persona_api_key",
        name="Persona",
        icon_slug="persona",
        color="#1c1c1c",
        description="Persona — identity verification + KYC.",
        hint="API key from Persona dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Persona API key"
            ),
        ],
    ),
    "zoominfo": APIKeyProvider(
        id="zoominfo_api_key",
        name="ZoomInfo",
        icon_slug="zoominfo",
        color="#1c1c1c",
        description="ZoomInfo — B2B contact + company database.",
        hint="API key from ZoomInfo dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="ZoomInfo API key"
            ),
        ],
    ),
    "sixtyfour": APIKeyProvider(
        id="sixtyfour_api_key",
        name="SixtyFour",
        icon_slug="sixtyfour",
        color="#1c1c1c",
        description="SixtyFour — AI research for lead enrichment.",
        hint="API key from SixtyFour dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="SixtyFour API key"
            ),
        ],
    ),
    "wiza": APIKeyProvider(
        id="wiza_api_key",
        name="Wiza",
        icon_slug="wiza",
        color="#1c1c1c",
        description="Wiza — LinkedIn scraper + email enrichment.",
        hint="API key from Wiza dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Wiza API key"
            ),
        ],
    ),
    "similarweb": APIKeyProvider(
        id="similarweb_api_key",
        name="SimilarWeb",
        icon_slug="similarweb",
        color="#1c1c1c",
        description="SimilarWeb — website + market intelligence.",
        hint="API key from SimilarWeb dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="SimilarWeb API key"
            ),
        ],
    ),
    "ahrefs": APIKeyProvider(
        id="ahrefs_api_key",
        name="Ahrefs",
        icon_slug="ahrefs",
        color="#1c1c1c",
        description="Ahrefs — SEO + backlinks + keyword research.",
        hint="API key from Ahrefs dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Ahrefs API key"
            ),
        ],
    ),
    "agentmail": APIKeyProvider(
        id="agentmail_api_key",
        name="AgentMail",
        icon_slug="agentmail",
        color="#1c1c1c",
        description="AgentMail — AI email agent (send, receive, thread).",
        hint="API key from AgentMail dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="AgentMail API key"
            ),
        ],
    ),
    "agentphone": APIKeyProvider(
        id="agentphone_api_key",
        name="AgentPhone",
        icon_slug="agentphone",
        color="#1c1c1c",
        description="AgentPhone — AI voice agent (make/receive calls).",
        hint="API key from AgentPhone dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="AgentPhone API key"
            ),
        ],
    ),
    "context_dev": APIKeyProvider(
        id="context_dev_api_key",
        name="Context",
        icon_slug="context_dev",
        color="#1c1c1c",
        description="Context — LLM answer analytics + user feedback.",
        hint="API key from Context dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Context API key"
            ),
        ],
    ),
    "cursor": APIKeyProvider(
        id="cursor_api_key",
        name="Cursor",
        icon_slug="cursor",
        color="#1c1c1c",
        description="Cursor — AI code editor. Background agents API.",
        hint="API key from Cursor dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Cursor API key"
            ),
        ],
    ),
    "devin": APIKeyProvider(
        id="devin_api_key",
        name="Devin",
        icon_slug="devin",
        color="#1c1c1c",
        description="Devin — Cognition AI software engineer agent.",
        hint="API key from Devin dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Devin API key"
            ),
        ],
    ),
    "mistral_parse": APIKeyProvider(
        id="mistral_api_key",
        name="Mistral OCR",
        icon_slug="mistral_parse",
        color="#1c1c1c",
        description="Mistral OCR — document parsing to markdown / structured data.",
        hint="API key from Mistral OCR dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Mistral OCR API key"
            ),
        ],
    ),
    "jina": APIKeyProvider(
        id="jina_api_key",
        name="Jina AI",
        icon_slug="jina",
        color="#1c1c1c",
        description="Jina — search, reader, embed via jina.ai.",
        hint="API key from Jina AI dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Jina AI API key"
            ),
        ],
    ),
    "reducto": APIKeyProvider(
        id="reducto_api_key",
        name="Reducto",
        icon_slug="reducto",
        color="#1c1c1c",
        description="Reducto — high-fidelity document parsing.",
        hint="API key from Reducto dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Reducto API key"
            ),
        ],
    ),
    "stagehand": APIKeyProvider(
        id="stagehand_api_key",
        name="Stagehand",
        icon_slug="stagehand",
        color="#1c1c1c",
        description="Stagehand — Browserbase AI browser automation.",
        hint="API key from Stagehand dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Stagehand API key"
            ),
        ],
    ),
    "brightdata": APIKeyProvider(
        id="brightdata_api_key",
        name="Bright Data",
        icon_slug="brightdata",
        color="#1c1c1c",
        description="Bright Data — proxy + web scraping API.",
        hint="API key from Bright Data dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Bright Data API key"
            ),
        ],
    ),
    "dspy": APIKeyProvider(
        id="dspy_api_key",
        name="DSPy Cloud",
        icon_slug="dspy",
        color="#1c1c1c",
        description="DSPy Cloud — prompt-program hosting + evaluation.",
        hint="API key from DSPy Cloud dashboard",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="DSPy Cloud API key"
            ),
        ],
    ),
    "datadog": APIKeyProvider(
        id="datadog_api_key",
        name="Datadog",
        icon_slug="datadog",
        color="#1c1c1c",
        description="Datadog — metrics, logs, events, monitors.",
        hint="From Datadog settings",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Datadog API key"
            ),
            CredentialField(
                id="app_key",
                label="Application Key",
                type="password",
                placeholder="Datadog application key",
            ),
        ],
    ),
    "new_relic": APIKeyProvider(
        id="new_relic_api_key",
        name="New Relic",
        icon_slug="new_relic",
        color="#1c1c1c",
        description="New Relic — APM, logs, metrics via NRQL + events.",
        hint="From New Relic settings",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="New Relic API key"
            ),
        ],
    ),
    "amplitude": APIKeyProvider(
        id="amplitude_api_key",
        name="Amplitude",
        icon_slug="amplitude",
        color="#1c1c1c",
        description="Amplitude — product analytics event ingestion.",
        hint="From Amplitude settings",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Amplitude API key"
            ),
            CredentialField(
                id="secret_key",
                label="Secret Key (for chart export)",
                type="password",
                placeholder="Amplitude secret key",
            ),
        ],
    ),
    "grafana": APIKeyProvider(
        id="grafana_api_key",
        name="Grafana Cloud",
        icon_slug="grafana",
        color="#1c1c1c",
        description="Grafana Cloud — dashboards, alerts, annotations, folders.",
        hint="From Grafana Cloud settings",
        fields=[
            CredentialField(
                id="api_key", label="Service Account Token", type="password", placeholder="glsa_..."
            ),
            CredentialField(
                id="stack", label="Stack subdomain", type="string", placeholder="mycompany"
            ),
        ],
    ),
    "langsmith": APIKeyProvider(
        id="langsmith_api_key",
        name="LangSmith",
        icon_slug="langsmith",
        color="#1c1c1c",
        description="LangSmith — LLM trace + evaluation platform.",
        hint="From LangSmith settings",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="LangSmith API key"
            ),
        ],
    ),
    "hex": APIKeyProvider(
        id="hex_api_key",
        name="Hex",
        icon_slug="hex",
        color="#1c1c1c",
        description="Hex — collaborative data notebooks + apps.",
        hint="From Hex settings",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Hex API key"
            ),
        ],
    ),
    "databricks": APIKeyProvider(
        id="databricks_api_key",
        name="Databricks",
        icon_slug="databricks",
        color="#1c1c1c",
        description="Databricks — SQL warehouses, jobs, notebooks.",
        hint="Databricks credentials",
        fields=[
            CredentialField(
                id="api_key", label="Personal Access Token", type="password", placeholder="dapi..."
            ),
            CredentialField(
                id="workspace_url",
                label="Workspace URL",
                type="string",
                placeholder="https://dbc-xxx.cloud.databricks.com",
            ),
        ],
    ),
    "clickhouse": APIKeyProvider(
        id="clickhouse_api_key",
        name="ClickHouse Cloud",
        icon_slug="clickhouse",
        color="#1c1c1c",
        description="ClickHouse Cloud — analytics DB via HTTP interface.",
        hint="ClickHouse Cloud credentials",
        fields=[
            CredentialField(id="username", label="Username", type="string", placeholder="default"),
            CredentialField(
                id="api_key", label="Password", type="password", placeholder="Password"
            ),
            CredentialField(
                id="host", label="Host", type="string", placeholder="https://xxx.clickhouse.cloud"
            ),
        ],
    ),
    "elasticsearch": APIKeyProvider(
        id="elasticsearch_api_key",
        name="Elasticsearch",
        icon_slug="elasticsearch",
        color="#1c1c1c",
        description="Elasticsearch — index, search, aggregate documents.",
        hint="Elasticsearch credentials",
        fields=[
            CredentialField(id="username", label="Username", type="string", placeholder="elastic"),
            CredentialField(
                id="api_key", label="Password / API Key", type="password", placeholder="Password"
            ),
            CredentialField(
                id="host",
                label="Host",
                type="string",
                placeholder="https://xxx.es.us-east-1.aws.elastic.cloud",
            ),
        ],
    ),
    "convex": APIKeyProvider(
        id="convex_api_key",
        name="Convex",
        icon_slug="convex",
        color="#1c1c1c",
        description="Convex — reactive backend / DB.",
        hint="Convex credentials",
        fields=[
            CredentialField(
                id="api_key", label="Deploy Key", type="password", placeholder="Deploy key"
            ),
            CredentialField(
                id="deployment_url",
                label="Deployment URL",
                type="string",
                placeholder="https://xxx.convex.cloud",
            ),
        ],
    ),
    "temporal": APIKeyProvider(
        id="temporal_api_key",
        name="Temporal Cloud",
        icon_slug="temporal",
        color="#1c1c1c",
        description="Temporal Cloud — workflow orchestration API.",
        hint="Temporal Cloud credentials",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Temporal Cloud API key"
            ),
        ],
    ),
    "railway": APIKeyProvider(
        id="railway_api_key",
        name="Railway",
        icon_slug="railway",
        color="#1c1c1c",
        description="Railway — deploy + manage services.",
        hint="Railway API access",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Railway API key"
            ),
        ],
    ),
    "dagster": APIKeyProvider(
        id="dagster_api_key",
        name="Dagster Cloud",
        icon_slug="dagster",
        color="#1c1c1c",
        description="Dagster Cloud — asset pipelines, jobs, runs.",
        hint="Dagster Cloud API access",
        fields=[
            CredentialField(
                id="api_key",
                label="Cloud API Token",
                type="password",
                placeholder="Dagster Cloud token",
            ),
            CredentialField(
                id="deployment", label="Deployment Slug", type="string", placeholder="prod"
            ),
        ],
    ),
    "daytona": APIKeyProvider(
        id="daytona_api_key",
        name="Daytona",
        icon_slug="daytona",
        color="#1c1c1c",
        description="Daytona — cloud dev environments.",
        hint="Daytona API access",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Daytona API key"
            ),
        ],
    ),
    "launchdarkly": APIKeyProvider(
        id="launchdarkly_api_key",
        name="LaunchDarkly",
        icon_slug="launchdarkly",
        color="#1c1c1c",
        description="LaunchDarkly — feature flags + segments.",
        hint="LaunchDarkly API access",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="LaunchDarkly API key"
            ),
        ],
    ),
    "incidentio": APIKeyProvider(
        id="incidentio_api_key",
        name="incident.io",
        icon_slug="incidentio",
        color="#1c1c1c",
        description="incident.io — incident response + postmortems.",
        hint="incident.io API access",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="incident.io API key"
            ),
        ],
    ),
    "rootly": APIKeyProvider(
        id="rootly_api_key",
        name="Rootly",
        icon_slug="rootly",
        color="#1c1c1c",
        description="Rootly — incident response, retros, integrations.",
        hint="Rootly API access",
        fields=[
            CredentialField(
                id="api_key", label="API Key", type="password", placeholder="Rootly API key"
            ),
        ],
    ),
}


def get_ai_providers() -> list[APIKeyProvider]:
    return [provider for provider in PROVIDERS.values() if provider.ai_provider_id]


def get_ai_provider(provider_id: str) -> APIKeyProvider | None:
    return next(
        (provider for provider in get_ai_providers() if provider.ai_provider_id == provider_id),
        None,
    )


def get_ai_provider_ids() -> set[str]:
    return {provider.ai_provider_id for provider in get_ai_providers() if provider.ai_provider_id}

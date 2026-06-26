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

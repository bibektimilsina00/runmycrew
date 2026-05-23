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
        icon_url: str,
        hint: str,
        fields: list[CredentialField],
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
        self.icon_url = icon_url
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
        description="Browser Use — AI-powered browser automation via browser-use.com",
        icon_url="https://cdn.brandfetch.io/browser-use.com/icon",
        hint="bu-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="bu-...")
        ],
    ),
    "airtable": APIKeyProvider(
        id="airtable_api_key",
        name="Airtable",
        description="Airtable — database and spreadsheet automation",
        icon_url="https://cdn.brandfetch.io/airtable.com/icon",
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
        description="Stripe — payments and billing automation",
        icon_url="https://cdn.brandfetch.io/stripe.com/icon",
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
        description="HubSpot — CRM contacts, deals, and companies",
        icon_url="https://cdn.brandfetch.io/hubspot.com/icon",
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
        description="Linear project management — create and manage issues",
        icon_url="https://cdn.brandfetch.io/linear.app/icon",
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
        description="Perplexity Sonar — web search + LLM with live internet access",
        icon_url="https://cdn.brandfetch.io/perplexity.ai/icon",
        hint="pplx-...",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="pplx-...")
        ],
    ),
    "elevenlabs": APIKeyProvider(
        id="elevenlabs_api_key",
        name="ElevenLabs",
        description="High-quality text-to-speech with voice cloning",
        icon_url="https://cdn.brandfetch.io/elevenlabs.io/icon",
        hint="API Key",
        fields=[
            CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")
        ],
    ),
    "notion": APIKeyProvider(
        id="notion_api_key",
        name="Notion",
        description="Connect to Notion using an Internal Integration Token",
        icon_url="https://cdn.brandfetch.io/notion.so/icon",
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
        description="Use your OpenAI API key for AI nodes",
        icon_url="https://cdn.brandfetch.io/openai.com/icon",
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
        description="Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku",
        icon_url="https://cdn.brandfetch.io/anthropic.com/icon",
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
        description="Gemini 1.5 Pro, Gemini 1.5 Flash",
        icon_url="https://cdn.brandfetch.io/google.com/icon",
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
        description="Llama 3, Mixtral, Gemma (Ultra-fast inference)",
        icon_url="https://cdn.brandfetch.io/groq.com/icon",
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
        description="Access many model providers through the OpenRouter API",
        icon_url="https://cdn.brandfetch.io/openrouter.ai/icon",
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
        description="DeepSeek chat and reasoning models",
        icon_url="https://cdn.brandfetch.io/deepseek.com/icon",
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
        description="Mistral chat and code models",
        icon_url="https://cdn.brandfetch.io/mistral.ai/icon",
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
        description="Grok models from xAI",
        icon_url="https://cdn.brandfetch.io/x.ai/icon",
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
        description="Open-source and hosted models through Together AI",
        icon_url="https://cdn.brandfetch.io/together.ai/icon",
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
        description="Jira — project management and issue tracking via REST API v3",
        icon_url="https://cdn.brandfetch.io/atlassian.com/icon",
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
        description="Salesforce — CRM records via Connected App access token",
        icon_url="https://cdn.brandfetch.io/salesforce.com/icon",
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
        description="Fast serverless inference for open-weight models",
        icon_url="https://cdn.brandfetch.io/fireworks.ai/icon",
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

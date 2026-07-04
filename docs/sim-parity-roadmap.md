# Sim-parity roadmap

Plan for closing the integration-coverage gap against Sim's catalog
(`temp/sim_nodes_triggers.md`). Last reviewed 2026-07-04.

## Executive summary

- **Sim catalog**: 268 blocks, 259 trigger events across 52 providers.
- **Shipped** (main + open PRs #290-#301): 184 registered node classes
  across 118 provider directories; 30+ trigger providers via polling
  and webhook; scaffolds cover REST / OAuth / polling / webhook with
  10 auth schemes.
- **Provider gap**: 117 real integrations remain (excluding system
  blocks + aliased names). Roadmap Phase 4.13-4.30 below enumerates
  every one, batched by vertical, ~5 per batch.
- **Trigger depth**: full sim parity via webhook for every shipped
  provider that has webhook events (Phases 4.9-4.12).

## Phase status

| Phase | Scope | State |
|---|---|---|
| 0 | Scaffolds + skill | **SHIPPED** — 4 PRs |
| 1 | 40 REST integrations | **SHIPPED** — 8 sub-PRs |
| 2 | 33 OAuth integrations | **SHIPPED** — 7 sub-PRs |
| 3 | 24 trigger providers (16 poll + 8 webhook) | **SHIPPED** — 5 sub-PRs |
| 4.1-4.12 | File node + trigger depth + long-tail (25 integrations) | **SHIPPED** — 12 open PRs (#290-#301) |
| 4.13-4.30 | Remaining 117 real integrations | **PLANNED** |

## Phase 0-3

See git history / merged PRs. Detailed specs preserved in the
[archive section](#archive-phase-0-3-detail) at the bottom.

## Phase 4 — Complete coverage

Roadmap now commits to full sim-block coverage. Every remaining real
integration listed, batched by vertical + auth pattern.

### Phase 4.1-4.12 — Shipped

| PR | Batch | Provider surface |
|---|---|---|
| #290 | 4.1 File node | `common.file` (read_url/write/append/parse) |
| #291 | 4.2 Trigger depth | jira 2→8, linear 3→8, notion 2→5 events |
| #292 | 4.3 Missing polls | attio (9 events) + salesforce (3 events) |
| #293 | 4.4 Confluence | action (10 ops) + polling (6 events) |
| #294 | 4.5 ServiceNow | action (10 ops) + polling (4/4 sim events) |
| #295 | 4.6 ATS | greenhouse + ashby (action + polling) |
| #296 | 4.7 Meeting-intel | grain + lemlist (action + polling) |
| #297 | 4.8 Outbound | instantly-trigger + emailbison (action + polling) |
| #298 | 4.9 Outbound webhooks | instantly + lemlist + emailbison webhooks |
| #299 | 4.10 Dev webhooks | jira + linear webhook (full sim parity) |
| #300 | 4.11 Docs webhooks | notion + confluence webhook (full sim parity) |
| #301 | 4.12 Deploy/forms | vercel + typeform webhook |

**Total in 4.1-4.12**: 25 integrations + trigger depth for 3 providers.

### Phase 4.13-4.30 — Planned

117 real remaining. Batched below by vertical. Each batch = 4-6
providers, action + polling/webhook where sim ships events. Estimated
1-2 PRs per batch.

#### 4.13 — Outbound webhook completion (5)
resend, sendgrid, mailgun, postmark, loops. All have action nodes
from Phase 1.2; add webhook triggers for delivery events. Svix scheme
for resend (new signature scheme in scaffold).

#### 4.14 — Data enrichment tier 1 (6)
apollo, clay, hunter, findymail, dropcontact, peopledatalabs. Bearer
auth. Standard REST — company/contact enrichment endpoints.

#### 4.15 — Data enrichment tier 2 (6)
datagma, enrich, enrichment, enrow, icypeas, leadmagic. Same pattern
as 4.14.

#### 4.16 — Email verification (5)
zerobounce, neverbounce, millionverifier, prospeo, persona. Single
op per provider (verify email). Simple REST.

#### 4.17 — B2B intel (5)
zoominfo, sixtyfour, wiza, similarweb, ahrefs. Bearer auth. Company
search + contact reveal.

#### 4.18 — AI agents / tools (6)
agentmail, agentphone, browser_use (variant), context_dev, cursor,
devin. AI coding agents + email/phone bots. All Bearer.

#### 4.19 — AI ecosystem (6)
mistral_parse, jina, reducto, stagehand, brightdata, dspy. Document
parsing, embeddings, headless browsing, agent frameworks.

#### 4.20 — Analytics/observability (6)
datadog, new_relic, amplitude, grafana, langsmith, hex. OAuth or API
key. Metrics + log push. Datadog needs API+APP key pair.

#### 4.21 — Data warehouses (5)
databricks, clickhouse, elasticsearch, convex, temporal. Bearer.
Query + collection ops.

#### 4.22 — Dev tooling (6)
railway, dagster, daytona, launchdarkly, incidentio, rootly. Bearer.
Deployment + feature flag + incident response.

#### 4.23 — Meeting intelligence (5)
circleback, evernote, extend, luma, granola. Similar shape to
grain/fathom. Bearer.

#### 4.24 — HR/finance (5)
rippling, workday, sap_concur, wealthbox, brex. OAuth mostly.
Some need SAML/SSO discovery.

#### 4.25 — Identity/security (5)
okta, clerk, onepassword, identity_center, infisical. OAuth
+ tenant-URL. Bulk user provisioning + secrets fetch.

#### 4.26 — Google surface completion (6)
google_ads, google_bigquery, google_maps, google_meet, google_translate,
google_vault. All under shared google_oauth. Some need per-service
scopes.

#### 4.27 — Google extras (3)
google_bigquery-extras, google_pagespeed, google_books, google_groups.

#### 4.28 — Microsoft/Atlassian gaps (4)
microsoft_ad, microsoft_dataverse, jira_service_management (jsm),
mothership. Reuse existing atlassian_api_key + microsoft_oauth
credentials.

#### 4.29 — Content/media (7)
youtube, wordpress, x (twitter), reddit, spotify, video_generator,
gamma. OAuth-heavy. wordpress needs xml-rpc option.

#### 4.30 — Long-tail misc (10)
tailscale, textract (aws), codepipeline (aws), trigger_dev, vanta,
kalshi, polymarket, quiver, sportmonks, revenuecat. Bearer auth,
1-2 ops each.

#### 4.31 — Comms + low-level protocols (7)
whatsapp, twilio_voice, smtp, sftp, ssh, arxiv, mcp. Some non-REST
— mcp needs SSE support; ssh/sftp use paramiko; smtp uses stdlib.

#### 4.32 — Miscellaneous (10)
agiloft, airweave, arxiv, ketch, latex, linkup, linq, obsidian, pi,
profound, pulse, quartr, greptile, guardrails, crowdstrike, cursor.
Cover in one sweep — all Bearer REST.

## Explicitly NOT shipping

These sim block ids don't map to our node architecture; they're
system features or naming aliases:

- **Aliases for existing nodes** (no new work needed):
  agent (→ ai.agent), athena (→ aws_athena), browser_use (→ ai.browser_use),
  condition (→ common.condition), evaluator (→ ai.evaluator), function
  (→ logic.code), iam (→ aws_iam), image_generator (→ ai.image_gen),
  knowledge (→ ai.knowledge), memory (→ ai.memory), mongodb (→ db.mongodb),
  mysql (→ db.mysql), openai/perplexity (→ ai.llm w/ provider),
  postgresql (→ db.postgres), rds (→ aws_rds), router (→ common.switch),
  schedule (→ common.cron), secrets_manager (→ aws_secrets_manager),
  ses (→ aws_ses), sqs (→ aws_sqs), sts (→ aws_sts), stt/tts/vision (→
  ai.stt/tts/vision), thinking (→ ai.thinking), wait (→ common.wait),
  webhook_request (→ http.webhook), workflow (→ logic.sub_workflow),
  google_calendar/contacts/docs/drive/forms/slides/tasks (→ gcalendar/
  gpeople/gdocs/gdrive/gforms/gslides/gtasks).

- **System / UI features** (not workflow nodes):
  credential, deployments, response, workflow_input, api_trigger,
  chat_trigger, start_trigger, starter, manual_trigger, input_trigger,
  variables, logs, note, table, appconfig, sim_workspace_event,
  generic_webhook, human_in_the_loop (→ have `logic.human_input`),
  parallel (→ have `logic.for_loop` + `logic.foreach`), api (→ have
  `http.request`).

- **Redis alias**: `redis` in sim = generic Redis; our `upstash_redis`
  is Upstash-specific. Add `db.redis` in 4.13 if user demand.

## Velocity + finish target

| Phase | Wall time (est) | Providers | Cumulative |
|---|---|---:|---:|
| 0 | 1-2 wk | 0 (foundation) | 83 |
| 1 | 3-4 wk | 40 | 123 |
| 2 | 3-4 wk | 20 | 143 |
| 3 | 2 wk | 20 | 163 |
| 4.1-4.12 | 3 wk | 25 | 188 |
| 4.13-4.32 | 6-8 wk | 117 | 305 |

Cumulative slightly overshoots sim's 268 because we split AWS + Google
into per-service dirs (aws_s3, aws_ses, ...) while sim keeps them
combined. Effective sim parity at end of 4.32: **100%**.

## Trigger event coverage

| Provider | Sim events | Ours | State |
|---|---:|---:|---|
| github | 11 | 3 | polling (from #262) |
| gitlab | 5 | 4 poll + 10 webhook | full |
| jira | 14 | 8 poll + 14 webhook | full |
| linear | 14 | 8 poll + 13 webhook | full |
| notion | 8 | 5 poll + 8 webhook | full |
| confluence | 22 | 6 poll + 22 webhook | full |
| monday | 9 | 6 poll | webhook pending 4.28 |
| attio | 21 | 9 poll | webhook variant not needed (poll covers) |
| salesforce | 5 | 3 poll | Streaming API webhook = future |
| servicenow | 4 | 4 poll | full parity |
| hubspot | 1 | 4 poll | full |
| asana | 2 | 2 poll | full |
| pagerduty | 5 | 3 poll | webhook variant = 4.30 |
| trello | 3 | 3 poll | webhook = 4.30 |
| calendly | 3 | 2 poll | webhook = 4.30 |
| calcom | 8 | 2 poll | webhook + depth = future |
| zendesk | 4 | 3 poll | full |
| telegram | 1 | 3 poll | full |
| outlook | 1 | 2 poll | full |
| intercom | 5 | 3 poll | webhook = 4.30 |
| grain | 7 | 5 poll | webhook variant = 4.23 |
| lemlist | 8 | 2 poll + 8 webhook | full parity |
| instantly | 20 | 3 poll + 18 webhook | full |
| emailbison | 17 | 2 poll + 10 webhook | mostly |
| vercel | 7 | 7 webhook | full parity |
| typeform | 1 | 1 webhook | full parity |
| ashby | 6 | 4 poll | webhook variant = 4.23 |
| azure_devops | 2 | 2 webhook | full |
| gong | 1 | 1 webhook | full |
| fathom | 1 | 1 webhook | full |
| fireflies | 1 | 1 webhook | full |
| twilio | 1 | 1 webhook | full |
| microsoft_teams | 1 | 1 webhook | full |
| webflow | 4 | 8 webhook | full+extras |

## Scaffold surface (what's built)

| Auth scheme | Providers |
|---|---|
| bearer | 40+ providers |
| header_token | linear, gitlab, klaviyo |
| basic | zendesk, jira, confluence, servicenow |
| basic_token_only | greenhouse, ashby |
| query_token | trello |
| aws_sigv4 | 10 AWS services |
| none (unauth) | rss |
| oauth2 code + refresh | 15 OAuth providers |

| Webhook signature scheme | Providers |
|---|---|
| hmac_sha256 | gitlab, github, notion, jira, confluence, gong, instantly, emailbison, vercel |
| hmac_sha1 | fireflies, vercel |
| hmac_sha256_b64 | microsoft_teams, typeform |
| stripe | stripe |
| shopify | shopify |
| gitlab_token | gitlab, fathom, azure_devops, lemlist |
| twilio | twilio |
| webflow | webflow |
| none | (URL-only providers) |

Scaffold features shipped:
- Manifest-driven REST/polling/webhook (Phase 0)
- SigV4 signing (Phase 2.3)
- Per-op extra headers (Phase 2.3)
- Per-provider scheduler token_fields (Phase 3.1)
- Verifier headers+URL kwargs (Phase 3.4)
- No-auth polling branch (Phase 3.5)
- Body-based event routing single + list form (Phase 4.9-4.12)
- URL-verification challenge handshake (Phase 4.11)

## Archive: Phase 0-3 detail

### Phase 0 — Scaffolds (4 PRs)

| PR | What | Validation |
|---|---|---|
| #263 | REST scaffold | airtable + linear |
| #264 | Polling scaffold | gpeople |
| #265 | Webhook scaffold | gitlab webhook |
| #266 | `/new-integration` skill | firecrawl |

### Phase 1 — REST sweep (40 integrations)

Batches 1.1-1.8: AI/scrape, email, search/data, devops/obs, DBs,
comms, CRM/sales, finalization. See merged PRs #267-#274.

### Phase 2 — OAuth majors (33 integrations)

Microsoft 365 (6), CRM/meetings (5 + hubspot), AWS (10), meetings +
docs (5), social/marketing (5), Planner + AWS completion (6), CRM
completion (3). PRs #275, #276, #278-#282.

### Phase 3 — Trigger sweep (24 providers)

Polling (16): gitlab, jira, linear, hubspot, asana (3.1); trello,
calendly, calcom, notion, intercom (3.2); zendesk, telegram,
outlook_mail (3.3); monday, rss, imap (3.5).

Webhook (8): azure_devops, twilio, microsoft_teams, webflow, gong,
fathom, fireflies (3.4). Plus pre-existing gitlab_webhook.

## Source

Sim catalog: `temp/sim_nodes_triggers.md` (auto-extracted 2026-06-26 —
268 blocks, 259 trigger events across 52 providers).

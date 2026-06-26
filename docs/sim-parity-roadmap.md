# Sim-parity roadmap

Plan for closing the integration-coverage gap against Sim's catalog
(`temp/sim_nodes_triggers.md`). Last reviewed 2026-06-26.

## Current gap

| Axis | Sim | Us | Gap | % |
|---|---:|---:|---:|---:|
| Total nodes | 268 | 83 | -185 | 31% |
| Core blocks (logic/AI) | 36 | ~30 | -6 | 83% |
| Tool integrations | 221 | 37 | -184 | 17% |
| Trigger blocks (dedicated) | 11 | 4 | -7 | 36% |
| Triggerable providers | 33 | ~12 | -21 | 36% |
| Trigger events total | 259 | ~50 | -209 | ~19% |

Core/logic close to parity. Tool integrations are the gap (~5–6× behind).
Trigger breadth ~3× behind.

## Strategy

Don't build 185 nodes by hand. Build scaffolds first (Phase 0), then
fan out via manifest-driven generation (Phase 1+). Per-node cost drops
from days → hours. Compound savings from PR ~30 onward.

## Phase 0 — Foundation (1–2 weeks, 4 PRs)

Cut per-integration cost. Detailed scope below.

### PR 0.1 — REST tool scaffold (4–5 days)

New ApiKey REST integration = manifest file only.

```
apps/api/app/node_system/scaffolds/
  rest_manifest.py        Pydantic types: FieldSpec, OpSpec, ProviderManifest
  rest_node_factory.py    build_rest_node(manifest) -> type[BaseNode]
  rest_dispatch.py        shared httpx wrapper + RESTError + auth header builder
  field_resolvers.py      {owner}/{repo} path-template substitution
apps/api/app/node_system/nodes/<provider>/
  manifest.py             provider manifest (data only)
  __init__.py             node = build_rest_node(MANIFEST)
```

ProviderManifest fields: `type`, `name`, `category`, `description`,
`icon_slug`, `color`, `base_url`, `credential_type`, `auth`,
`auth_header_name`, `auth_value_template`, `public_ops`, `fields`,
`operations`.

OpSpec: `id`, `label`, `method`, `path`, `public`, `query_fields`,
`body_fields`, `body_template`, `output_flatten`.

Acceptance: port airtable + linear to manifest. LOC drops ~80%.
Smoke tests stay green.

### PR 0.2 — Polling trigger scaffold (3 days)

```
apps/api/app/node_system/scaffolds/
  polling_manifest.py
  polling_node_factory.py
  polling_cursor.py       diff_known_ids / diff_since_timestamp / diff_last_sha
```

PollingEvent fields: `id`, `label`, `list_path`, `list_params`,
`cursor_strategy` (`known_ids` | `since_timestamp` | `last_sha`),
`id_field`, `filter_expr` (JMESPath), `flatten`, `fields`.

Acceptance: port `github_trigger.py` to manifest (5 events). ~480 LOC
→ ~50 LOC manifest. Identical scheduler registration + cursor
behavior.

### PR 0.3 — Webhook trigger scaffold (3–4 days)

Single shared receiver. Per-provider manifest declares signature scheme +
event header + dropdown options.

```
apps/api/app/node_system/scaffolds/
  webhook_manifest.py
  webhook_node_factory.py
apps/api/app/features/webhooks/
  router.py               POST /webhooks/{provider}/{workflow_id}/{node_id}
  service.py              lookup node -> verify -> filter -> dispatch
  signature_schemes.py    hmac_sha256, hmac_sha1, stripe, shopify, none
```

SignatureSpec: `scheme`, `header_name`, `secret_field`, `prefix`.
WebhookTriggerManifest: `type`, `name`, `provider`, `signature`,
`event_header`, `events`, `extra_fields`, `payload_shape` (JSONPath).

Acceptance: port `github_webhook.py` to manifest. Add `gitlab_webhook`
manifest to prove the pattern.

### PR 0.4 — Skill update: `/new-integration` (2 days)

One command emits manifest + registry entry + smoke test + credential
provider entry + loadOptions stubs.

Args: `--auth=apikey|oauth|none`, `--base-url`, `--icon-slug`,
`--color`, `--ops=op1,op2,…`, `--triggers=poll,webhook`.

Generates files under `apps/api/app/node_system/nodes/<provider>/`,
adds entry to `credential_manager/api_keys.py`, adds registry line in
`registry/registry.py`, emits `apps/api/tests/test_<provider>_smoke.py`.

Acceptance: `/new-integration firecrawl --auth=apikey
--base-url=https://api.firecrawl.dev/v1 --ops=scrape,crawl,map` →
PR-able branch in <2 min, smoke green.

### Phase 0 validation gates

Before Phase 1 starts:
1. Port airtable + linear via REST manifest — metadata snapshot identical.
2. Port github_trigger via polling manifest — same outputs, scheduler entry intact.
3. Port github_webhook via webhook manifest — signature + filter unchanged.
4. Run `/new-integration` end-to-end on firecrawl, ship as test PR.

If any port fails or skill is rough — fix in Phase 0, don't carry forward.

### Phase 0 risks

- **Manifest expressiveness ceiling.** Some ops (Slack auth modes, GitHub
  GraphQL) won't fit pure manifest. Plan: ~85% via manifest, ~15% drop down
  to custom handlers registered alongside.
- **Pydantic prop union explosion.** Many ops with disjoint fields. Use
  `model_config = ConfigDict(extra='ignore')`, all fields Optional. Validate
  with airtable (~25 union fields) before scaling.
- **loadOptions endpoints stay bespoke.** Skill emits stubs; humans fill in.
- **Metadata snapshot tests.** Add
  `apps/api/tests/test_node_metadata_snapshot.py` locking every registered
  node's metadata shape. Catches accidental drift during ports.

## Phase 1 — High-leverage ApiKey REST sweep (3–4 weeks)

40 integrations via REST scaffold. Velocity ~10/week with parallel agents.

Targets (priority order, may reshuffle by demand):

- AI/scrape: firecrawl, exa, tavily, jina, serper, huggingface,
  mistral_parse, apify, brightdata, stagehand, reducto
- Email/marketing: resend, sendgrid, mailgun, mailchimp, loops, instantly,
  lemlist, smtp
- Search/data: wikipedia, arxiv, duckduckgo, brandfetch
- Comms: twilio_sms, twilio_voice, sendblue
- DBs (URL-config): supabase, redis (upstash), clickhouse, elasticsearch,
  pinecone, qdrant, tinybird, convex
- Misc: posthog, sentry, dub, typeform, shopify, square, wordpress, reddit, x

## Phase 2 — OAuth majors (3–4 weeks)

~20 integrations. Hardest per-node, highest user value.

- Microsoft 365 (shared OAuth provider): outlook, microsoft_teams,
  sharepoint, onedrive, microsoft_excel, microsoft_planner
- AWS family (shared SigV4 + access-key credential): s3, ses, sqs, rds,
  secrets_manager, iam, sts, athena, cloudwatch, cloudformation
- CRM/sales OAuth: pipedrive, attio, asana, trello, monday, intercom, zendesk
- Meetings: zoom, calendly, calcom
- Docs: dropbox, box, docusign

## Phase 3 — Trigger sweep (2 weeks)

20 trigger-capable providers. With polling + webhook scaffolds, ~1–2 hrs each.

Polling: gitlab, jira, linear, hubspot, asana, trello, monday, calendly,
calcom, pagerduty, zendesk, telegram, outlook (mail), rss (generic).

Webhook: gitlab, azure_devops, twilio (SMS), microsoft_teams, webflow,
gong, fathom, fireflies.

Plus a generic IMAP polling trigger — covers outlook + arbitrary email hosts.

## Phase 4 — Long tail (ongoing)

~100 niche integrations (sap_s4hana, workday, servicenow, identity_center,
…). Demand-driven, no speculative builds.

Also in this phase:
- Core block gaps: Function block, Deployments block, File block
- Per-integration depth: bring our notion/slack/etc. to sim op count parity

## Velocity targets

| Phase | Wall time | Net new nodes | Cumulative |
|---|---|---:|---:|
| 0 — Scaffold | 1–2 wk | 0 (foundation) | 83 |
| 1 — REST sweep | 3–4 wk | ~40 | ~123 |
| 2 — OAuth majors | 3–4 wk | ~20 | ~143 |
| 3 — Triggers | 2 wk | ~20 | ~163 |
| 4 — Long tail | ongoing | demand | trends → 268 |

End of Phase 3: ~60% sim parity.

## Source

Sim catalog: `temp/sim_nodes_triggers.md` (auto-extracted 2026-06-26 —
268 blocks, 259 trigger events across 52 providers).

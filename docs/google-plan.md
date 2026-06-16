# Google Integration — Plan

Mirrors the shape of the Meta build: one consolidated OAuth provider per
surface family, per-surface trigger + action nodes, end-to-end test
matrix scored 🔒 / ⚠️ / ✅ per cell. This doc is the plan + the tracker.

## Inventory — what exists today

- **`GoogleOAuthProvider`** in `apps/api/app/credential_manager/oauth/flow.py`
  - id: `google_oauth`
  - scopes (current): `gmail.send`, `gmail.readonly`, `openid`, `email`, `profile`
  - no Calendar / Drive / Sheets / Docs / Tasks scopes yet
- **Nodes registered:**
  - `action.gmail` — send_email, search, get_email, list_labels, get_profile
  - `action.google_sheets` — get_spreadsheet, get_values, update_values, append_values, clear_values
  - `trigger.google_sheets` — TBD shape (polling? push?)
- **Missing:**
  - Gmail trigger (new email arrived)
  - Calendar surface entirely
  - Drive surface entirely
  - Docs surface entirely
  - Tasks, Forms, YouTube, Contacts (People), Meet — phase 2+

## Auth model

Most surfaces use **OAuth** with the user's Google account. A handful
take API keys, service accounts, or extra developer tokens. Fuse maps
each pattern to its own credential type:

| Cred type           | Surfaces                                                                 |
|---------------------|--------------------------------------------------------------------------|
| `google_oauth`      | Gmail, Calendar, Drive, Sheets, Docs, Slides, Tasks, Forms, YouTube, Contacts, Chat, Photos, Business Profile, Analytics, Search Console, AdSense, BigQuery, Cloud Storage, Pub/Sub, Translate, Vision, Speech, Document AI, Dialogflow |
| `google_api_key`    | Maps / Places / Geocoding (no per-user context — workspace-shared key)   |
| `google_ads_oauth`  | Google Ads (OAuth + an extra `developer-token` header — sibling provider for clarity) |
| `google_service_account` | BigQuery / Cloud APIs when the user wants a service-account workflow (Phase 6) |

Default for everything except Maps / Ads → `google_oauth`. One OAuth
credential per Google account covers every surface the user grants.
Scopes are **incremental** — a user who only connects "Gmail" gets a
gmail-only token; a power user grants Drive + Sheets + Calendar in
the same dialog and gets one wider token.

Reasons to mirror Meta's two-cred pattern across every Google surface?
**No.** Google's single account model lets us collapse most of it into
`google_oauth`. The narrow exceptions above each get their own provider
so the cred picker UI surfaces the right credentials to the right nodes.

### Configuration plan

In Google Cloud Console → **OAuth Consent Screen**:
- App name, support email, app logo, scopes list, test users
- Required for the OAuth dialog to render anything other than the
  account picker

In Google Cloud Console → **APIs & Services → Library**: enable the
APIs we call. Each Fuse surface gates on one or more APIs:

| Surface              | API to enable                              |
|----------------------|--------------------------------------------|
| Gmail                | Gmail API                                  |
| Calendar             | Google Calendar API                        |
| Drive                | Google Drive API                           |
| Sheets               | Google Sheets API                          |
| Docs                 | Google Docs API                            |
| Slides               | Google Slides API                          |
| Tasks                | Google Tasks API                           |
| YouTube              | YouTube Data API v3                        |
| Contacts             | People API                                 |
| Forms                | Google Forms API                           |
| Meet                 | Google Meet API (limited program)          |
| Chat                 | Google Chat API                            |
| Photos               | Photos Library API                         |
| Business Profile     | Google Business Profile API                |
| Analytics 4          | Google Analytics Data API                  |
| Search Console       | Search Console API                         |
| Ads                  | Google Ads API                             |
| AdSense              | AdSense Management API                     |
| BigQuery             | BigQuery API                               |
| Cloud Storage        | Cloud Storage JSON API                     |
| Pub/Sub              | Pub/Sub API                                |
| Translate            | Cloud Translation API                      |
| Vision               | Cloud Vision API                           |
| Speech               | Cloud Speech-to-Text + Text-to-Speech      |
| Document AI          | Document AI API                            |
| Dialogflow           | Dialogflow CX API                          |
| Maps / Places        | Maps JavaScript / Places API / Geocoding   |
| reCAPTCHA            | reCAPTCHA Enterprise API                   |
| Firebase / Identity  | Identity Toolkit + Firebase Admin          |
| Admin SDK            | Admin SDK API                              |
| Vault                | Vault API                                  |

Per-API scopes table is below.

## Phased rollout

### Phase 1 — Email + Calendar (highest-frequency automations)

- Gmail trigger: **new message in inbox** (matching query)
- Gmail action: send, reply, search, get, list_labels, get_profile, add_label, remove_label, mark_read, delete, trash
- Calendar trigger: **new event created** / **upcoming event** / **event updated**
- Calendar action: create_event, update_event, delete_event, list_events, find_free_slots, send_response

### Phase 2 — Data ops (Sheets + Drive + Docs)

- Sheets trigger: **new row appended** (polling) / **row updated** (polling)
- Sheets action: extend existing — add `clear_range`, `create_sheet`, `find_replace`, `batch_update`
- Drive trigger: **new file in folder** (polling) / **file shared with me**
- Drive action: upload, download, list, share, move, delete, create_folder, search
- Docs trigger: comment_added (push via Drive Activity API)
- Docs action: create, append_text, find_replace, insert_image

### Phase 3 — Social / CRM / Tasks

- YouTube trigger: new comment on video, new subscriber
- YouTube action: post comment, reply, update video metadata, upload
- Contacts (People) action: create_contact, search, update, list
- Tasks action: create_task, list, complete, update
- Forms trigger: new response

### Phase 4 — Specialised / SaaS-ops

- Slides (create deck, append slide, find/replace text, export pdf)
- Meet (create meeting, list participants)
- Chat (send DM / send to space, threaded reply)
- Photos (list album, upload photo, search by date)
- Google Tasks (already in Phase 3, double-listed for clarity)
- Keep (list notes, create note) — limited API

### Phase 5 — Marketing / Analytics / Cloud

- **Business Profile (Google My Business)** — list locations, reply to reviews, post updates, fetch insights
- **Analytics 4** — run report (event counts, sessions, conversions by dimension), list properties
- **Search Console** — fetch search analytics, submit sitemap, list URL inspection
- **Ads** — list campaigns, pause/enable, fetch metrics, create campaign (heavyweight API)
- **AdSense / AdMob** — earnings reports
- **BigQuery** — run SQL, list datasets, insert rows (for data-pipeline workflows)
- **Cloud Storage** — upload/download object, list bucket (distinct from Drive; used by code/data folks)
- **Pub/Sub** — publish message (also used internally as a trigger transport)

### Phase 6 — AI / Maps / Auth

- **Translate** — translate text, detect language
- **Vision** — OCR, label detection, safe-search, face detect
- **Speech** — speech-to-text, text-to-speech
- **Document AI** — extract structured fields from invoices, forms, IDs
- **Dialogflow CX** — agent intent detection
- **Maps / Places** — geocoding, place lookup, distance matrix, directions
- **reCAPTCHA Enterprise** — verify token (for workflows guarding form input)
- **Identity Platform / Firebase Auth** — user mgmt for embedded auth flows

### Phase 7 — Workspace Admin (B2B)

- **Admin SDK Directory** — create/suspend user, list groups, add member, reset password
- **Admin SDK Reports** — audit logs, usage reports
- **Vault** — eDiscovery (legal hold), exports
- **Cloud Identity** — group/membership mgmt across orgs

### Out of scope

These exist but aren't useful enough for our user base to prioritise:

- Classroom (education-specific)
- AdMob (mobile-ads-specific)
- Sites (deprecated by Google)
- Workspace Add-ons SDK (different shape — runs *inside* Google's UI)

## Scopes per surface

| Surface | Scopes |
|---|---|
| Gmail (read + send + labels) | `gmail.modify` (covers read+send+labels+threads) — or fine-grained: `gmail.readonly` + `gmail.send` + `gmail.labels` + `gmail.modify` |
| Calendar | `calendar` (read+write) or `calendar.events` (events only) |
| Drive | `drive.file` (only files the user creates via the app) is safer; `drive` is full access (requires verification) |
| Sheets | `spreadsheets` (read+write) |
| Docs | `documents` (read+write) |
| Slides | `presentations` |
| Tasks | `tasks` |
| YouTube | `youtube.readonly` + `youtube.force-ssl` (post + comment) |
| Contacts | `contacts` or `contacts.readonly` |
| Forms | `forms.body.readonly` + `forms.responses.readonly` |
| Profile | `openid` + `email` + `profile` |
| Chat | `chat.messages` + `chat.spaces` |
| Photos | `photoslibrary.readonly` / `photoslibrary.appendonly` |
| Business Profile | `business.manage` |
| Analytics 4 | `analytics.readonly` |
| Search Console | `webmasters.readonly` (or `webmasters` for sitemap submit) |
| Ads | `adwords` (note: separate developer token required) |
| AdSense | `adsense.readonly` |
| BigQuery | `bigquery` (or `bigquery.readonly`) |
| Cloud Storage | `devstorage.read_write` (or `devstorage.read_only`) |
| Pub/Sub | `pubsub` |
| Cloud APIs (Translate / Vision / Speech / Doc AI / Dialogflow) | `cloud-platform` (single broad scope; per-API enable governs access) |
| Maps / Places / Geocoding | API key (no OAuth) — separate `GOOGLE_MAPS_API_KEY` env |
| reCAPTCHA Enterprise | `cloud-platform` |
| Admin SDK | `admin.directory.user` + `admin.directory.group` (+ `.member` for membership) |
| Vault | `ediscovery` |

Restricted scopes (Drive full, Gmail modify) trigger Google's
**Restricted Scope Verification** (CASA / security review). Plan to
ship with non-restricted scopes by default and gate the full-access
operations behind opt-in.

## Trigger delivery options

Google has three patterns:

1. **Polling** — Fuse hits the API on a schedule. Cheap, no setup,
   works for Sheets row appends, Drive folder changes, Calendar
   upcoming events. Higher latency.
2. **Push notifications** (Drive, Calendar, Gmail watch) — Fuse calls
   `watch` API which registers a webhook URL + channel id; Google
   POSTs on change with a header indicating the resource. Lower
   latency, needs renewal every ~7 days, needs a webhook callback
   endpoint same shape as our Meta one.
3. **Pub/Sub** (Gmail, Drive) — Google publishes to a Pub/Sub topic
   we subscribe to. Most reliable, requires GCP project + topic +
   subscription. Heavy setup.

**Phase 1 plan:** polling for everything. Add push/Pub/Sub once a
real user asks for sub-minute latency. Keeps initial implementation
contained.

## Per-surface node design

Mirror the Meta pattern:

- One **trigger node** per surface (`trigger.google.{gmail,calendar,drive,sheets,docs,...}`) with `event_type` dropdown
- One **action node** per surface (`action.google.{gmail,calendar,...}`) with `operation` dropdown
- Condition-driven field visibility

### Gmail node sketch

Triggers (`event_type`):
- new_message — query string filter (`from:` / `subject:` / `label:`)
- new_thread — same query
- new_label — when a label gets attached to anything

Actions (`operation`):
- send_email — to, cc, bcc, subject, body, body_type (plain/html), attachments (media field — reuses our `MediaRenderer`)
- reply — thread_id, body
- forward — message_id, to, body
- search — query, max_results
- get_message — id, format (full / metadata / minimal)
- list_labels
- add_label — message_id, label_id
- remove_label — message_id, label_id
- mark_read / mark_unread — message_id
- trash / untrash — message_id
- create_label — name, color
- get_profile

### Calendar node sketch

Triggers:
- event_created — calendar_id (default: primary)
- event_updated — calendar_id
- event_starting_soon — calendar_id, lead_time_minutes (10 / 30 / 60)
- event_cancelled — calendar_id

Actions:
- create_event — calendar_id, summary, description, start, end, attendees, location, conference_create
- update_event — event_id + fields
- delete_event — event_id
- list_events — calendar_id, time_min, time_max, q
- find_free_slots — calendars[], duration_minutes, time_min, time_max
- respond — event_id, response_status (accepted / declined / tentative)

### Drive node sketch

Triggers:
- new_file_in_folder — folder_id, mime_type filter
- file_modified — folder_id
- file_shared_with_me

Actions:
- upload — name, parent_folder_id, mime_type, source (media field), make_public
- download — file_id
- list — folder_id, query
- share — file_id, email, role (reader/commenter/writer)
- move — file_id, target_folder_id
- delete — file_id
- create_folder — name, parent_folder_id
- search — query

### Sheets node sketch (extend existing)

Triggers (new):
- new_row — spreadsheet_id, sheet_name (polling interval setting)
- row_updated — spreadsheet_id, sheet_name (polling, compares snapshots)

Actions (extend existing):
- get_spreadsheet, get_values, update_values, append_values, clear_values (have these)
- create_spreadsheet — title, sheets[]
- create_sheet — spreadsheet_id, title
- duplicate_sheet — spreadsheet_id, source_sheet_id, new_title
- find_replace — spreadsheet_id, find, replace, sheet_name (optional), match_case
- batch_update — spreadsheet_id, requests[] (raw API request list)

### Docs node sketch

Actions:
- create — title, content (plain text)
- append_text — document_id, text
- insert_image — document_id, image_url (media field), index
- find_replace — document_id, find, replace, match_case
- get — document_id (returns parsed text)
- export — document_id, format (pdf / docx / html / txt)

## Test matrix (will fill as we build)

| # | Surface | Trigger / Action | Status | Notes |
|---|---------|------------------|--------|-------|
| 1 | gmail | trigger: new_message (polling) | ⏳ | |
| 2 | gmail | action: send_email | ⏳ | text body |
| 3 | gmail | action: send_email + attachment | ⏳ | media field reuse |
| 4 | gmail | action: reply | ⏳ | |
| 5 | gmail | action: search | ⏳ | |
| 6 | gmail | action: add_label | ⏳ | |
| 7 | gmail | action: mark_read | ⏳ | |
| 8 | gmail | action: trash | ⏳ | |
| 9 | calendar | trigger: event_created | ⏳ | polling |
| 10 | calendar | trigger: event_starting_soon | ⏳ | |
| 11 | calendar | action: create_event | ⏳ | with attendees |
| 12 | calendar | action: update_event | ⏳ | |
| 13 | calendar | action: delete_event | ⏳ | |
| 14 | calendar | action: list_events | ⏳ | |
| 15 | calendar | action: find_free_slots | ⏳ | |
| 16 | drive | trigger: new_file_in_folder | ⏳ | polling |
| 17 | drive | action: upload | ⏳ | media field |
| 18 | drive | action: download | ⏳ | returns signed url |
| 19 | drive | action: list | ⏳ | |
| 20 | drive | action: share | ⏳ | |
| 21 | drive | action: create_folder | ⏳ | |
| 22 | sheets | trigger: new_row | ⏳ | polling |
| 23 | sheets | action: get_values | ✅ | already exists — re-verify |
| 24 | sheets | action: append_values | ✅ | already exists — re-verify |
| 25 | sheets | action: create_spreadsheet | ⏳ | |
| 26 | sheets | action: find_replace | ⏳ | |
| 27 | docs | action: create | ⏳ | |
| 28 | docs | action: append_text | ⏳ | |
| 29 | docs | action: find_replace | ⏳ | |
| 30 | docs | action: export pdf | ⏳ | |

Statuses: ⏳ not started · 🔄 in progress · ✅ proven end-to-end ·
🔒 blocked by external (verification, API enable, scope review) · ⚠️
partial / works with caveats

## External setup checklist

Before any of this code runs:

1. **GCP project** — pick existing or create one. Hold its project id.
2. **OAuth Consent Screen** — App name `Fuse`, support email, app
   logo, all scopes from the table above listed under "Scopes for
   Google APIs". Add yourself as a **test user** during dev.
3. **OAuth client** — Web application, redirect URI:
   `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/google/callback`
   (and `http://localhost:8000/...` for local). Grab client id + secret.
4. **Enable APIs** — every API from the per-surface table.
5. `.env`:
   - `GOOGLE_CLIENT_ID=...`
   - `GOOGLE_CLIENT_SECRET=...`
6. **Verification** — for restricted scopes only (Drive full, Gmail
   modify). Skip until needed.

## Open questions

- Polling cadence: per-trigger setting, or global cron interval? Lean
  per-trigger so noisy triggers can be slower.
- Cursor storage: where do we keep "last seen message id" for the
  Gmail trigger? Probably MetaSubscription-equivalent table —
  `IntegrationTriggerState(workflow_id, node_id, cursor: jsonb)`.
- Sheets trigger: snapshot whole sheet on first run, then diff each
  poll, or rely on the spreadsheet's revision history? Diff is
  expensive on large sheets; revision is cheaper but only tells
  modified vs not.
- Attachment download for Gmail trigger: do we eagerly fetch + store
  as Assets, or pass a fetch URL for the action to consume?
  Lean **eager-as-Assets** for parity with the Meta media model.

## What to build first

1. Extend `GoogleOAuthProvider` to request all Phase-1 scopes
   (`gmail.modify` + `calendar` + `drive.file` + `spreadsheets` +
   `documents` + `tasks` + `openid email profile`) under a single
   incremental dialog.
2. Add `IntegrationTriggerState` table for polling-based triggers.
3. Add a polling scheduler that drives Google triggers on a per-node
   interval. Reuse Celery beat.
4. Build the **Gmail surface** first — most-asked node category in
   automation tools. Trigger + actions + attachment reuse of our
   MediaRenderer.
5. Then Calendar — second-most.
6. Sheets extensions + Drive + Docs after.

## Notes from the Meta build that apply here

- Lock the `media` field reuse early — it's the right primitive for
  both Gmail attachments and Drive upload.
- Listen-mode for triggers: same `/listen` endpoint pattern works
  for polling triggers too, just runs a single poll against Google
  the moment the user clicks Run.
- Auto-config pieces (like our Get Started button install): for
  Google watch-channel triggers, auto-call `watch()` and store the
  channel id + resource id for renewal.
- Per-surface webhook callback: when we move to push notifications,
  add `/webhooks/google/{kind}` endpoints. Match the Meta `app_id`
  pattern with `kind ∈ {drive, gmail, calendar}` so each Google
  resource type routes to its own signature/verification path.

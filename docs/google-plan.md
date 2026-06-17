# Google Integration — Plan

Mirrors the shape of the Meta build: one consolidated OAuth provider per
surface family, per-surface trigger + action nodes, end-to-end test
matrix scored 🔒 / ⚠️ / ✅ per cell. This doc is the plan + the tracker.

## Status snapshot (2026-06-17)

- **Phase 1 (Gmail + Calendar)** — ✅ shipped
- **Phase 2 (Sheets + Drive + Docs)** — ✅ shipped
- **Phase 3 (Tasks + Forms + Contacts + YouTube)** — ✅ shipped
  (originally only Tasks/Forms/Contacts/YouTube; we promoted YouTube
  out of Phase 3 in the original draft and ended up shipping it here)
- **Phase 4 (Slides + Chat)** — Slides ✅ shipped; Chat ✅ shipped.
  Phase 4 is fully closed out.
  Dropped from Phase 4: **Photos** (niche personal-media),
  **Meet** (API barely exists — Calendar already auto-creates Meet
  links, and post-call transcripts are too niche to carry the surface),
  **Keep** (read-only stub API).
- **Phase 5 (Marketing / Analytics / Cloud)** — **Analytics 4 ✅ shipped.**
  Business Profile, Search Console, BigQuery, Cloud Storage ⏳ pending.
  **AdSense** dropped (too niche). **Ads** deferred (heavyweight,
  developer-token flow). **Pub/Sub** kept only as an internal
  transport, not user-facing.
- **Phase 6 (AI / Maps)** — Translate, Vision, Speech, Maps/Places
  ⏳ pending. **Document AI** deferred (Vision OCR covers common
  cases). **Dialogflow CX** dropped (the LLM node already handles
  intent detection). **Admin SDK** deferred (B2B-only, narrow).
  **reCAPTCHA**, **Identity Toolkit**, **Vault** dropped (auth /
  eDiscovery — off-mission for workflow automation).

Cross-cutting infrastructure (also shipped this cycle):

- ✅ Generic **`google-file` picker** (Sheets / Docs / Slides / Forms
  mimes — one renderer, picks any Google-native file by mime, with
  inline “Create new” CTA wired to `/credentials/{id}/google-files`).
- ✅ `gsheet-tab`, `gtasks-tasklist`, `gpeople-group`, `youtube-video`,
  `youtube-playlist`, `youtube-channel` pickers (resource-specific
  dropdowns w/ search + optional inline create).
- ✅ Generic **`datetime` field type** — text input + native picker;
  `granularity: "date" | "datetime"` typeOption. Used by Tasks `due`,
  Sheets list filters, Forms `submitted_after`, Contacts birthday,
  YouTube `publishedAfter` / `publishedBefore`.
- ✅ **MediaRenderer overhaul** — one unified bar (URL / Upload /
  Library) with autofill `nameField` typeOption. Used by Drive upload,
  Docs `insert_image`, YouTube `upload_video` + thumbnail, Forms
  (future), etc.
- ✅ **Integration polling scheduler** with provider registry,
  listen-mode slot driver, exponential backoff, and listen-then-poll
  hand-off. Eight providers registered so far.
- ✅ **YouTube RSS feed parser** — zero-quota new-video detection on
  any public channel via the Atom feed at
  `https://www.youtube.com/feeds/videos.xml?channel_id=…`.

## Inventory — what exists today

OAuth provider: **`GoogleOAuthProvider`** in
`apps/api/app/credential_manager/oauth/flow.py`. Scope set (single
incremental consent):

```
gmail.modify, calendar, drive.file, spreadsheets, documents, tasks,
forms.body, forms.responses.readonly, contacts,
youtube.force-ssl, youtube.upload, presentations,
chat.messages, chat.messages.reactions,
chat.spaces.readonly, chat.memberships.readonly,
analytics.readonly,
openid, email, profile
```

`GOOGLE_DRIVE_WATCH_EXTERNAL=true` swaps `drive.file` → `drive`
(Restricted scope; needs CASA).

### Nodes registered

Triggers ✅

- `trigger.gmail` (gmail)
- `trigger.gcal_event` (gcalendar)
- `trigger.gdrive_change` (gdrive) — `changes.list?pageToken` real-time
- `trigger.google_sheets` (google_sheets) — `row_added` + `row_updated`
- `trigger.gtasks_change` (google_tasks) — `task_added` + `task_completed`
- `trigger.gforms_response` (google_forms) — `new_response`
- `trigger.gpeople_change` (google_people) — `contact_added` +
  `contact_updated` (etag-based)
- `trigger.gyt_change` (google_youtube) — `new_comment`, `new_subscriber`,
  `new_video` (Data API **or RSS**), `new_video_search_match`,
  `new_reply_to_my_comment`
- `trigger.gchat_change` (google_chat) — `new_message_in_space`
  (createTime-cursor polling, optional CEL extra-filter)

Actions ✅

- `action.gmail` (Gmail)
- `action.gcal` (Calendar)
- `action.gdrive` (Drive — 7 ops + folder picker + custom server-proxied browser)
- `action.google_sheets` (Sheets — 21 ops incl. row CRUD, find/replace,
  sort/format/auto-resize, share, export)
- `action.gdocs` (Docs — 19 ops)
- `action.gtasks` (Tasks — 12 ops; date-padding fix for bare YYYY-MM-DD)
- `action.gforms` (Forms — 16 ops; responses already mapped to
  `{question_title: value}`)
- `action.gpeople` (Contacts — 12 ops; emails/phones/addresses accept
  bare-string OR `{value, type}` dict shapes)
- `action.gyt` (YouTube — 28 ops incl. multipart **video upload**,
  thumbnail upload, comment moderation)
- `action.gslides` (Slides — 24 ops incl. create-from-outline for
  AI-driven deck generation, batch slide ops, text/shape/image insert,
  speaker notes, background fills)
- `action.gchat` (Chat — 12 ops: send / update / delete / list / get
  messages, list spaces + members, find DM, add / list / delete
  reactions; full Card v2 forwarding, thread-key replies)
- `action.ga4` (Analytics 4 — 13 ops: run_report / run_realtime_report /
  run_pivot_report / batch_run_reports / check_compatibility /
  get_metadata + Admin reads: list_accounts / list_properties /
  get_property / list_data_streams / list_key_events /
  list_custom_dimensions / list_custom_metrics. Property picker
  groups by account. Read-only — `analytics.readonly` scope)

Still **missing** (after the prune — see status snapshot for what
was dropped or deferred)

- Phase 4: ✅ fully shipped
- Phase 5: Business Profile, Search Console, BigQuery, Cloud Storage
- Phase 6: Translate, Vision, Speech, Maps/Places

**Deferred** (kept in roadmap, low priority): Ads, Document AI,
Admin SDK. **Pub/Sub** only as an internal transport (not a user-facing
node).

## Auth model

Most surfaces use **OAuth** with the user's Google account. A handful
take API keys, service accounts, or extra developer tokens. Fuse maps
each pattern to its own credential type:

| Cred type           | Surfaces                                                                 |
|---------------------|--------------------------------------------------------------------------|
| `google_oauth`      | Gmail, Calendar, Drive, Sheets, Docs, Slides, Tasks, Forms, YouTube, Contacts, Chat, Business Profile, Analytics, Search Console, BigQuery, Cloud Storage, Pub/Sub, Translate, Vision, Speech, Document AI |
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

| Surface              | API to enable                              | Status |
|----------------------|--------------------------------------------|--------|
| Gmail                | Gmail API                                  | ✅ |
| Calendar             | Google Calendar API                        | ✅ |
| Drive                | Google Drive API                           | ✅ |
| Sheets               | Google Sheets API                          | ✅ |
| Docs                 | Google Docs API                            | ✅ |
| Tasks                | Google Tasks API                           | ✅ |
| Forms                | Google Forms API                           | ✅ |
| Contacts             | People API                                 | ✅ |
| YouTube              | YouTube Data API v3                        | ✅ |
| Slides               | Google Slides API                          | ✅ |
| Chat                 | Google Chat API                            | ✅ |
| Business Profile     | Google Business Profile API                | ⏳ |
| Analytics 4          | Google Analytics Data API + Admin API      | ✅ |
| Search Console       | Search Console API                         | ⏳ |
| BigQuery             | BigQuery API                               | ⏳ |
| Cloud Storage        | Cloud Storage JSON API                     | ⏳ |
| Translate            | Cloud Translation API                      | ⏳ |
| Vision               | Cloud Vision API                           | ⏳ |
| Speech               | Cloud Speech-to-Text + Text-to-Speech      | ⏳ |
| Maps / Places        | Maps JavaScript / Places API / Geocoding   | ⏳ |
| Pub/Sub              | Pub/Sub API                                | 🛠 internal transport only |
| Ads                  | Google Ads API                             | 🕓 deferred |
| Document AI          | Document AI API                            | 🕓 deferred |
| Admin SDK            | Admin SDK API                              | 🕓 deferred |
| Meet                 | Google Meet API (limited program)          | ❌ dropped |
| Keep                 | Google Keep API                            | ❌ dropped |
| Photos               | Photos Library API                         | ❌ dropped |
| AdSense              | AdSense Management API                     | ❌ dropped |
| Dialogflow           | Dialogflow CX API                          | ❌ dropped |
| reCAPTCHA            | reCAPTCHA Enterprise API                   | ❌ dropped |
| Firebase / Identity  | Identity Toolkit + Firebase Admin          | ❌ dropped |
| Vault                | Vault API                                  | ❌ dropped |

Per-API scopes table is below.

## Phased rollout

### ✅ Phase 1 — Email + Calendar (shipped)

- ✅ Gmail trigger: **new message in inbox** (matching query)
- ✅ Gmail action: send, reply, search, get, list_labels, add_label,
  remove_label, mark_read, trash, plus standard CRUD
- ✅ Calendar trigger: **event_created** / **event_starting_soon** /
  **event_updated**
- ✅ Calendar action: create_event, update_event, delete_event,
  list_events, find_free_slots, respond

### ✅ Phase 2 — Data ops (Sheets + Drive + Docs) (shipped)

Sheets — 21 ops, two triggers:

- ✅ Sheets trigger: `row_added` (count cursor) and `row_updated`
  (per-row SHA-1 hash cursor)
- ✅ Sheets actions: get_spreadsheet, get_values, update_values,
  append_values, clear_values, create_spreadsheet, create_sheet,
  duplicate_sheet, delete_sheet, find_replace, batch_update,
  lookup_row (header-aware), add_row (`{header: value}` dict),
  update_row, delete_row, rename_sheet, share, export (PDF/XLSX/
  CSV/ODS/HTML), sort_range, format_range (bold/italic/colour/number),
  auto_resize_columns

Drive — full action set + real-time change feed:

- ✅ Drive trigger: `gdrive_change` via `changes.list?pageToken=…` —
  no search-index lag; classifier handles added / modified / trashed
- ✅ Drive actions: upload (`media` field), download, list, share,
  rename, delete, create_folder, search, plus the custom server-proxied
  folder browser that sidesteps adblockers

Docs — 19 ops (no trigger yet):

- ✅ create / get_text / get_with_structure / copy / rename / delete /
  share / export (PDF/DOCX/HTML/TXT/EPUB/ODT/RTF)
- ✅ append_text / insert_text / find_replace / delete_range /
  format_text (bold/italic/underline/strikethrough/font/colour) /
  set_paragraph_style (heading + alignment + indent)
- ✅ insert_image (media field) / insert_table / insert_page_break
- ✅ set_header / set_footer
- ⏳ Docs trigger (comment_added via Drive Activity API) — deferred

### ✅ Phase 3 — Tasks + Forms + Contacts + YouTube (shipped)

Tasks — 12 ops + 2 trigger events:

- ✅ Tasks trigger: `task_added` (id-set cursor) + `task_completed`
  (per-id boolean state cursor)
- ✅ Tasks actions: list_tasklists / create / rename / delete tasklist;
  list_tasks / get_task / create_task / update_task / complete_task /
  delete_task / move_task / clear_completed

Forms — 16 ops + new_response trigger:

- ✅ Forms trigger: `new_response` — cursor `{last_submitted_at}`,
  response answers auto-mapped to `{question_title: value}` via the
  form structure
- ✅ Forms actions: create / get_form / update_form_info /
  update_settings (quiz mode + email collection) / delete / share /
  add_text_question / add_choice_question (RADIO/CHECKBOX/DROP_DOWN
  + shuffle) / add_date_question / add_scale_question /
  add_file_upload_question (max files + size + types) /
  add_section_break / delete_item / move_item /
  list_responses (datetime-picker filter) / get_response

Contacts (People API) — 12 ops + 2 trigger events:

- ✅ Contacts trigger: `contact_added` (resource-name set) +
  `contact_updated` (etag map — People API bumps etag on every change)
- ✅ Contacts actions: list_contacts (sortable, paginated, configurable
  personFields) / search_contacts (substring) / get / create /
  update (auto-fetches current etag before PATCH) / delete /
  list_other_contacts; list_groups / create_group / delete_group /
  add_to_group / remove_from_group (batched)

YouTube — 28 action ops + 5 trigger events:

- ✅ YouTube trigger:
  - `new_comment` (cursor `{known_thread_ids}`; per-video or
    channel-wide)
  - `new_subscriber` (cursor `{known_subscriber_ids}`)
  - `new_video` — **two backends**: own channel via Data API uploads
    playlist, OR any public channel via the **RSS feed** (zero quota)
  - `new_video_search_match` (cursor `{last_published_at}`; description
    advises ≥5 min poll interval — 100 quota units per call)
  - `new_reply_to_my_comment`
- ✅ YouTube actions:
  - Videos (9): list_my_videos, get_video, get_video_rating,
    **upload_video** (media field, single-chunk multipart), update_video,
    delete_video, rate_video, set_video_thumbnail (media field),
    search_videos (query + publishedAfter/Before via datetime renderer
    + region + duration + sort)
  - Playlists (7): list / create / update / delete /
    add_video_to_playlist (with optional position) /
    remove_video_from_playlist / list_playlist_items
  - Comments (7): list_comments, post_top_comment, reply_to_comment,
    update_comment, delete_comment, mark_comment_as_spam,
    set_comment_moderation_status (held/published/rejected + optional
    ban author)
  - Channels (2): get_my_channel, get_channel_by_id
  - Subscriptions (3): list / subscribe / unsubscribe

### Phase 4 — Specialised / SaaS-ops

- ✅ **Slides** (24 ops: create deck, append slide, find/replace text,
  export PDF, set speaker notes, duplicate slide, delete slide,
  **create_from_outline** for AI-driven decks, batch updates,
  text/shape/image insert, background fills)
- ✅ **Chat** (12 ops: send_message — text + Card v2 + thread key,
  update_message, delete_message, list_messages, get_message,
  list_spaces, get_space, list_members, find_direct_message,
  add_reaction, list_reactions, delete_reaction). Trigger
  `trigger.gchat_change` with `new_message_in_space` over
  `createTime > cursor` polling, optional CEL extra-filter for
  sender-based scoping. Shipped under user OAuth — no bot-app install
  required.
- ❌ **Meet — dropped.** API barely exists — Calendar already
  auto-creates Meet links on event create, and the rest of the API
  (post-call conference records / transcripts) is too niche to carry
  the surface. Revisit if transcript-driven workflows surface real
  demand.
- ❌ **Keep — dropped.** API is a read-only stub; no automation hook
  worth the OAuth scope.
- ❌ **Photos — dropped.** Workflow-automation use cases for personal
  media (auto-backup, social-sync) are niche; quota + scope overhead
  doesn't pay back for a B2B automation surface.

### ⏳ Phase 5 — Marketing / Analytics / Cloud

- **Business Profile (GMB)** — list locations, reply to reviews, post
  updates, fetch insights
- **Analytics 4** — run report (event counts, sessions, conversions by
  dimension), list properties
- **Search Console** — fetch search analytics, submit sitemap, list
  URL inspection
- **BigQuery** — run SQL, list datasets, insert rows
- **Cloud Storage** — upload/download object, list bucket
- 🛠 **Pub/Sub** — kept only as the internal trigger-transport
  substrate; not exposed as a user-facing publish/subscribe node.
- 🕓 **Ads — deferred.** High marketing value but big OAuth lift
  (separate `developer-token` header, sibling provider). Revisit
  after the rest of Phase 5 ships.
- ❌ **AdSense / AdMob — dropped.** Earnings reports for ad
  publishers — tiny audience for a horizontal automation platform.

### ⏳ Phase 6 — AI / Maps

- **Translate** — translate text, detect language
- **Vision** — OCR, label detection, safe-search, face detect
- **Speech** — speech-to-text, text-to-speech
- **Maps / Places** — geocoding, place lookup, distance matrix,
  directions
- 🕓 **Document AI — deferred.** Heavyweight processor-based setup;
  Vision OCR covers the common "extract text from receipt" case.
- ❌ **Dialogflow CX — dropped.** The LLM node already handles intent
  detection / conversational routing with far less Google-specific
  setup.
- ❌ **reCAPTCHA Enterprise — dropped.** Token verification is an
  auth concern, not workflow material.
- ❌ **Identity Platform / Firebase Auth — dropped.** User
  management for embedded auth flows is off-mission for workflow
  automation.

### 🕓 Phase 7 — Workspace Admin (B2B, deferred)

Whole phase deferred until B2B-onboarding demand surfaces. When it
does, the only kept surface is:

- 🕓 **Admin SDK Directory / Reports** — create/suspend user, list
  groups, audit logs.

Dropped from this phase:

- ❌ **Vault — dropped.** eDiscovery / legal hold is a regulated
  niche, separate buyer, separate trust requirements.
- ❌ **Cloud Identity — dropped.** Group / membership mgmt across orgs
  is a Workspace admin concern, not workflow automation.

### Out of scope

- Classroom (education-specific)
- AdMob (mobile-ads-specific)
- Sites (deprecated by Google)
- Workspace Add-ons SDK (different shape — runs *inside* Google's UI)

## Scopes per surface

| Surface | Scopes | Status |
|---|---|---|
| Gmail (read + send + labels) | `gmail.modify` | ✅ in OAuth scope set |
| Calendar | `calendar` | ✅ |
| Drive | `drive.file` (default); `drive` behind `GOOGLE_DRIVE_WATCH_EXTERNAL` | ✅ |
| Sheets | `spreadsheets` | ✅ |
| Docs | `documents` | ✅ |
| Tasks | `tasks` | ✅ |
| Forms | `forms.body` + `forms.responses.readonly` | ✅ |
| Contacts | `contacts` | ✅ |
| YouTube | `youtube.force-ssl` + `youtube.upload` | ✅ |
| Profile | `openid` + `email` + `profile` | ✅ |
| Slides | `presentations` | ✅ |
| Chat | `chat.messages` + `chat.messages.reactions` + `chat.spaces.readonly` + `chat.memberships.readonly` | ✅ |
| Business Profile | `business.manage` | ⏳ |
| Analytics 4 | `analytics.readonly` | ✅ |
| Search Console | `webmasters.readonly` (or `webmasters` for sitemap submit) | ⏳ |
| BigQuery | `bigquery` (or `bigquery.readonly`) | ⏳ |
| Cloud Storage | `devstorage.read_write` (or `devstorage.read_only`) | ⏳ |
| Pub/Sub | `pubsub` | 🛠 internal transport only |
| Cloud APIs (Translate / Vision / Speech) | `cloud-platform` (single broad scope; per-API enable governs access) | ⏳ |
| Maps / Places / Geocoding | API key (no OAuth) — separate `GOOGLE_MAPS_API_KEY` env | ⏳ |
| Ads | `adwords` (separate developer token required) | 🕓 deferred |
| Document AI | `cloud-platform` | 🕓 deferred |
| Admin SDK | `admin.directory.user` + `admin.directory.group` (+ `.member` for membership) | 🕓 deferred |
| Meet | `meetings.space.created` | ❌ dropped |
| Keep | `keep` | ❌ dropped |
| Photos | `photoslibrary.readonly` / `photoslibrary.appendonly` | ❌ dropped |
| AdSense | `adsense.readonly` | ❌ dropped |
| Dialogflow | `cloud-platform` | ❌ dropped |
| reCAPTCHA Enterprise | `cloud-platform` | ❌ dropped |
| Identity Platform / Firebase Auth | `cloud-platform` | ❌ dropped |
| Vault | `ediscovery` | ❌ dropped |

Restricted scopes (Drive full, Gmail modify) trigger Google's
**Restricted Scope Verification** (CASA / security review). We ship
with non-restricted scopes by default and gate the full-access
operations behind opt-in.

## Trigger delivery options

Google has three patterns:

1. **Polling** — Fuse hits the API on a schedule. Cheap, no setup. ✅
   This is what every shipped Google trigger uses. Provider registry +
   listen-mode driver covered in
   `apps/api/app/execution_engine/scheduler/integration_polling.py` and
   `apps/api/app/features/triggers/polling_listener.py`.
2. **Push notifications** (Drive, Calendar, Gmail watch) — Google POSTs
   on change. Lower latency, ~7-day channel TTL, needs a webhook
   endpoint same shape as the Meta one. ⏳ Deferred until a user asks
   for sub-minute latency.
3. **Pub/Sub** (Gmail, Drive) — heaviest setup, most reliable. ⏳
   Deferred.

**`new_video` over RSS** counts as a fourth path — uses YouTube's
public Atom feed for zero quota. Not generalisable to other surfaces
(only YouTube exposes feeds like this).

## Per-surface node design

Pattern that all shipped Google surfaces follow:

- One **trigger node** per surface (`trigger.google.{gmail,gcal_event,
  gdrive_change,google_sheets,gtasks_change,gforms_response,
  gpeople_change,gyt_change}`) with `event_type` dropdown when there
  are ≥2 events
- One **action node** per surface (`action.{gmail,gcal,gdrive,
  google_sheets,gdocs,gtasks,gforms,gpeople,gyt}`) with `operation`
  dropdown
- Condition-driven field visibility
- Pickers reused: `google-file` (Sheets/Docs/Slides/Forms via mime
  typeOption), `gsheet-tab`, `gtasks-tasklist`, `gpeople-group`,
  `youtube-video`, `youtube-playlist`, `youtube-channel`
- `datetime` field for any RFC3339 input, with `granularity` typeOption
- `media` field for any binary attachment (Drive upload, Docs
  insert_image, YouTube upload + thumbnail)

## Test matrix

| # | Surface | Trigger / Action | Status | Notes |
|---|---------|------------------|--------|-------|
| 1 | gmail | trigger: new_message (polling) | ✅ | |
| 2 | gmail | action: send_email | ✅ | |
| 3 | gmail | action: send_email + attachment | ✅ | media field reuse |
| 4 | gmail | action: reply | ✅ | |
| 5 | gmail | action: search | ✅ | |
| 6 | gmail | action: add_label | ✅ | |
| 7 | gmail | action: mark_read | ✅ | |
| 8 | gmail | action: trash | ✅ | |
| 9 | calendar | trigger: event_created | ✅ | polling |
| 10 | calendar | trigger: event_starting_soon | ✅ | |
| 11 | calendar | action: create_event | ✅ | with attendees |
| 12 | calendar | action: update_event | ✅ | |
| 13 | calendar | action: delete_event | ✅ | |
| 14 | calendar | action: list_events | ✅ | |
| 15 | calendar | action: find_free_slots | ✅ | |
| 16 | drive | trigger: gdrive_change | ✅ | `changes.list` real-time |
| 17 | drive | action: upload | ✅ | media field |
| 18 | drive | action: list | ✅ | |
| 19 | drive | action: share | ✅ | |
| 20 | drive | action: create_folder | ✅ | |
| 21 | sheets | trigger: row_added | ✅ | populated row count cursor |
| 22 | sheets | trigger: row_updated | ✅ | per-row SHA-1 hash cursor |
| 23 | sheets | action: get_values / append_values | ✅ | |
| 24 | sheets | action: create_spreadsheet | ✅ | |
| 25 | sheets | action: find_replace / sort_range / format_range | ✅ | |
| 26 | sheets | action: lookup_row / add_row / update_row | ✅ | header-aware |
| 27 | sheets | action: share / export PDF | ✅ | |
| 28 | docs | action: create / append_text | ✅ | |
| 29 | docs | action: find_replace | ✅ | |
| 30 | docs | action: insert_image (media field) | ✅ | |
| 31 | docs | action: format_text + set_paragraph_style | ✅ | |
| 32 | docs | action: set_header / set_footer | ✅ | two-step batchUpdate |
| 33 | docs | action: export PDF / DOCX | ✅ | |
| 34 | tasks | action: list / create_task | ✅ | |
| 35 | tasks | action: update_task / complete_task | ✅ | date padding fix |
| 36 | tasks | trigger: task_added / task_completed | ✅ | |
| 37 | forms | trigger: new_response | ✅ | answers auto-mapped to titles |
| 38 | forms | action: create + add_*_question | ✅ | all 6 question kinds |
| 39 | forms | action: list_responses (datetime filter) | ✅ | |
| 40 | contacts | action: list / search / create / update | ✅ | |
| 41 | contacts | action: list_groups + add_to_group | ✅ | |
| 42 | contacts | trigger: contact_added / contact_updated | ✅ | etag cursor |
| 43 | youtube | action: list_my_videos / get_video | ✅ | |
| 44 | youtube | action: upload_video + set_thumbnail | ✅ | multipart upload |
| 45 | youtube | action: post_top_comment / reply / moderate | ✅ | full comment surface |
| 46 | youtube | action: playlists CRUD + items | ✅ | |
| 47 | youtube | action: subscribe / unsubscribe | ✅ | |
| 48 | youtube | trigger: new_comment | ✅ | |
| 49 | youtube | trigger: new_subscriber | ✅ | |
| 50 | youtube | trigger: new_video (Data API + RSS) | ✅ | RSS = zero quota |
| 51 | youtube | trigger: new_video_search_match | ✅ | quota-aware |
| 52 | youtube | trigger: new_reply_to_my_comment | ✅ | |
| 53 | slides | action: create + append slide | ✅ | 24 ops total |
| 54 | slides | action: find_replace_text | ✅ | |
| 55 | slides | action: export PDF | ✅ | |
| 56 | slides | action: create_from_outline | ✅ | AI-driven deck gen |
| 57 | slides | action: set_speaker_notes | ✅ | empty-shape deleteText guarded |
| 58 | slides | action: update_background | ✅ | OpaqueColor vs OptionalColor split |
| 59 | chat | action: send_message (text + thread_key) | ✅ | user OAuth, no bot install |
| 60 | chat | action: send_message with cardsV2 | ✅ | dict / list / JSON string accepted |
| 61 | chat | action: update_message / delete_message | ✅ | updateMask=text |
| 62 | chat | action: list_messages / get_message | ✅ | createTime filter, orderBy |
| 63 | chat | action: list_spaces / get_space / list_members | ✅ | space-type CEL filter |
| 64 | chat | action: find_direct_message | ✅ | users/{id} lookup |
| 65 | chat | action: add_reaction / list_reactions / delete_reaction | ✅ | unicode emoji |
| 66 | chat | trigger: new_message_in_space | ✅ | createTime-cursor polling |
| 67 | business_profile | action: list_locations / reply_review | ⏳ | |
| 68 | business_profile | trigger: new_review | ⏳ | |
| 69 | analytics4 | action: run_report (dimensions + metrics + date range) | ✅ | accepts comma list or JSON array |
| 70 | analytics4 | action: run_realtime_report | ✅ | last-30-minute slice |
| 71 | analytics4 | action: run_pivot_report / batch_run_reports | ✅ | pivots forwarded verbatim |
| 72 | analytics4 | action: check_compatibility / get_metadata | ✅ | self-service dimension discovery |
| 73 | analytics4 | admin: list_accounts / list_properties / get_property | ✅ | account-scoped filter |
| 74 | analytics4 | admin: list_data_streams / list_key_events | ✅ | web + iOS + Android streams |
| 75 | analytics4 | admin: list_custom_dimensions / list_custom_metrics | ✅ | user-defined fields |
| 76 | search_console | action: get_search_analytics | ⏳ | |
| 77 | bigquery | action: run_sql | ⏳ | |
| 78 | cloud_storage | action: upload / download object | ⏳ | |
| 79 | translate | action: translate_text | ⏳ | |
| 80 | vision | action: ocr / labels | ⏳ | |
| 81 | speech | action: stt / tts | ⏳ | |
| 82 | maps | action: geocode / distance_matrix | ⏳ | API-key cred |

Statuses: ⏳ not started · 🔄 in progress · ✅ proven end-to-end ·
🔒 blocked by external (verification, API enable, scope review) · ⚠️
partial / works with caveats · 🛠 internal substrate (not user-facing)
· 🕓 deferred · ❌ dropped

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

## Open questions (still open)

- Push-notification migration for Drive / Gmail / Calendar — desired
  before or after Phase 4 wraps?
- Per-trigger poll-interval defaults: we set 60s baseline + bumped
  search-heavy events to 300+. Do we expose a workspace-wide minimum?
- Cursor migration when we add new event types to existing triggers
  (e.g. adding `comment_deleted` to YouTube later) — the
  `event_type` mismatch already resnapshots cleanly, so we're fine
  on the engine side; UI might want a toast.
- Workspace-shared `GOOGLE_MAPS_API_KEY` lifecycle — auto-rotate or
  expose to admins?

## Notes from the build (apply forward)

- Lock the `media` field reuse early — it's the right primitive for
  Gmail attachments, Drive upload, Docs `insert_image`, YouTube
  upload + thumbnail, Slides insert (Phase 4).
- The `google-file` picker is the right primitive for any
  Drive-resident Google-native file (set the mime via typeOption).
- The `datetime` field with `granularity` typeOption is reusable
  anywhere we touch RFC3339.
- Listen-mode for triggers: same `/listen` endpoint pattern works for
  polling triggers; the editor's Run button auto-routes to `/listen`
  when the graph contains any registered polling trigger.
- Auto-config pieces (like the Get Started button install): for
  webhook-based Google triggers (Phase 5+), auto-call `watch()` and
  store the channel id + resource id for renewal.
- Per-surface webhook callback: when we move to push notifications,
  add `/webhooks/google/{kind}` endpoints. Match the Meta `app_id`
  pattern with `kind ∈ {drive, gmail, calendar}` so each Google
  resource type routes to its own signature/verification path.
- YouTube's RSS approach (no auth, no quota) is unique to YouTube —
  don't try to generalise it.

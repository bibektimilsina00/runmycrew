# Meta Integration — Test Matrix

End-to-end test plan for every Meta trigger and action node. Use the Meta
Dashboard **Test** button on each webhook field so the full pipeline
(webhook → slot claim → execution engine → node call) runs in Development
mode without waiting for App Review / Live.

## Apps

| App | App ID | Credential type in Fuse | Webhook URL |
|---|---|---|---|
| Fuse (parent) | `861560943689175` | `meta_oauth` | `https://fuse.bibektimilsina.tech/api/v1/webhooks/meta/861560943689175` |
| Fuse-IG (child) | `1317058520562350` | `instagram_oauth` | `https://fuse.bibektimilsina.tech/api/v1/webhooks/meta/1317058520562350` |

Verify token (both apps): the value of `META_WEBHOOK_VERIFY_TOKEN` in `.env`.

## Pre-flight (one-time, before any test)

1. Tunnel up: `curl -s https://fuse.bibektimilsina.tech/api/v1/webhooks/meta/861560943689175?hub.mode=subscribe&hub.challenge=PING&hub.verify_token=<TOKEN>` returns `PING`.
2. `.env` has:
   - `META_WEBHOOK_LOOSE_LISTEN_MATCH=true` (dev — lets slot fire when Meta's id namespace doesn't match the cred's stored ids)
   - `META_APP_ID`, `META_APP_SECRET`, `META_INSTAGRAM_APP_ID`, `META_INSTAGRAM_APP_SECRET`, `META_WEBHOOK_VERIFY_TOKEN`
3. Each surface's webhook is configured in its own use-case dashboard (see `docs/meta-setup.md`).
4. A real credential exists in Fuse for each surface you plan to test.
5. Test IG account + a second IG account are both Instagram Testers on the Fuse-IG app and have accepted the invite.

## Per-test loop

For every cell in the matrix:

1. Open the workflow → drop the trigger node → set credential + target resource + event_type → wire to the action node → save.
2. Click **Run** in Fuse — Listen slot opens (or `/run` fires if no Meta trigger).
3. Open Meta App Dashboard → relevant product → Webhook fields → click **Test** next to the field listed in the table.
4. Watch uvicorn — expect:
   - `POST /api/v1/webhooks/meta/<APP_ID> 200`
   - `Meta webhook routing tuple: object=... target_id=0 field=...`
   - `id-namespace fallback claimed 1 slot(s)` (test mode shortcut)
   - `1 workflow(s) triggered`
5. Watch Celery worker — expect `Executing node <trigger>` → `Executing node <action>` → terminal status.
6. Fuse UI Logs panel — trigger row + action row visible, click each to inspect Input/Output.

Action nodes are exercised by their parent trigger's Test event. Real Meta API calls inside actions will usually error (synthetic ids aren't real accounts), but the request shape, credential resolution, template rendering, and error surfacing are still verified end-to-end.

---

## 1. Instagram

Webhook config: Dashboard → app `Fuse` → use case **Manage messaging & content on Instagram**.

Two flows:
- **API setup with Facebook login** → wires the parent app (`861560943689175`) → for `meta_oauth` credentials.
- **API setup with Instagram login** → wires the child app (`1317058520562350`) → for `instagram_oauth` credentials.

Trigger node: `trigger.meta.instagram` · Action node: `action.meta.instagram` · Target prop: `ig_account_id`.

| # | Cred type | Trigger event_type | Webhook field to click | Action operation | Notes |
|---|---|---|---|---|---|
| 1 | `meta_oauth` | comment | `comments` | reply_comment | Reply target = `=$step.comment_id` |
| 2 | `meta_oauth` | message | `messages` | send_dm | Recipient = `=$step.from_id` |
| 3 | `meta_oauth` | mention | `mentions` | send_dm | — |
| 4 | `meta_oauth` | story_reply | `messages` | send_dm | Real shape arrives wrapped in `messaging[].message.reply_to.story` |
| 5 | `meta_oauth` | story_mention | `messages` | send_dm | Real shape carries `attachments[].type=story_mention` |
| 6 | `meta_oauth` | (any) | (any) | publish_post (IMAGE) | Needs public image URL in `media_url` |
| 7 | `meta_oauth` | (any) | (any) | publish_post (VIDEO) | Public MP4 URL |
| 8 | `meta_oauth` | (any) | (any) | publish_post (REELS) | Public MP4 URL |
| 9 | `meta_oauth` | (any) | (any) | publish_story | Public image/video URL |
| 10 | `instagram_oauth` | comment | `comments` | reply_comment | Same as #1 but via child app webhook |
| 11 | `instagram_oauth` | message | `messages` | send_dm | Real DMs land as `message_edit` envelope in Dev mode — text is empty until Live |
| 12 | `instagram_oauth` | mention | `mentions` | send_dm | — |
| 13 | `instagram_oauth` | story_reply | `messages` | send_dm | — |
| 14 | `instagram_oauth` | story_mention | `messages` | send_dm | — |

Test events deliver `target_id=0` → loose match fallback claims the slot.

## 2. Facebook (Page + Messenger)

Webhook config: Dashboard → app `Fuse` → use cases:
- **Manage everything on your Page** → Page object
- **Engage with customers on Messenger from Meta** → Page object (Messenger DMs come via Page subscription)

Trigger node: `trigger.meta.facebook` · Action node: `action.meta.facebook` · Target prop: `page_id` · Cred type: `meta_oauth`.

| # | Trigger event_type | Webhook field | Action operation | Notes |
|---|---|---|---|---|
| 15 | comment | `feed` | reply_comment | `feed` envelope has many sub-types — filter by `value.item == 'comment'` happens inside `_flatten_entry` |
| 16 | message | `messages` (Messenger product) | send_message (messaging_type=RESPONSE) | Within 24h window |
| 17 | message | `messages` | send_message (messaging_type=MESSAGE_TAG) | Outside 24h, tag required |
| 18 | mention | `mention` | reply_comment | — |
| 19 | postback | `messaging_postbacks` | send_message | Triggered by user clicking persistent menu / Get Started |
| 20 | reaction (any) | `feed` | reply_comment | Reaction envelopes piggyback on `feed` with `verb == 'react'` |
| 21 | reaction (filtered: like) | `feed` | (none) | Subtype filter exercises the reaction-filter dropdown |
| 22 | (any) | (any) | publish_post | Posts text-only to the Page |

## 3. WhatsApp

Webhook config: Dashboard → app `Fuse` → use case **Connect with customers through WhatsApp** → Webhooks → **Whatsapp Business Account** object.

Trigger node: `trigger.meta.whatsapp` · Action node: `action.meta.whatsapp` · Target prop: `waba_id` · Cred type: `meta_oauth`.

| # | Trigger event_type | Webhook field | Action operation | Notes |
|---|---|---|---|---|
| 23 | message | `messages` | send_text | Recipient = `=$step.from_phone` |
| 24 | message | `messages` | send_template | Template name + language code required. `loadOptions` pulls templates from `/meta/wa/templates` |
| 25 | message | `messages` | mark_read | Message id = `=$step.message_id` |
| 26 | status (any) | `messages` | (none) | Status envelopes share the `messages` field |
| 27 | status (filtered: delivered) | `messages` | (none) | Subtype filter dropdown |

## 4. Lead Ads

Webhook config: Dashboard → app `Fuse` → use case **Capture & manage ad leads with Marketing API** → Webhooks → **Page** object → `leadgen` field.

Trigger node: `trigger.meta.lead` · Action node: `action.meta.lead` · Target prop: `page_id` · Cred type: `meta_oauth`.

| # | Trigger event_type | Webhook field | Action operation | Notes |
|---|---|---|---|---|
| 28 | submission | `leadgen` | fetch | Fetch action calls `/{leadgen_id}` to pull full form answers |

## Tracking

Status legend per row: `⏳` not started · `🔄` in progress · `✅` passes Test webhook + action call · `❌` fails (note error)

| # | Status | Last run uvicorn line | Notes |
|---|---|---|---|
| 1 | ✅ | webhook + slot claim + reply_comment template resolve OK | action errors at Meta API with fake comment id `17865799348089039` — expected in Test mode |
| 2 | ⚠️ | Meta dashboard Test on `messages` field doesn't fire for parent-app Instagram product (silent) | Pipeline identical to cells #1 / #11 — covered transitively. Real DMs deliver via Page subscribed_apps route in Live mode |
| 3 | ✅ | `1 workflow(s) triggered` via mentions field | template wire-up to action verified via this cell |
| 4 | ⏳ | | |
| 5 | ⏳ | | |
| 6 | ✅ | Real IG post created — id `18592381312028392`. Media fetched via signed public asset URL | first true production-style E2E — uploaded asset → signed URL → Meta → live post |
| 7 | ⏭️ | covered transitively via #6 (same _publish_post path, video_url branch) | retest with real Live mode |
| 8 | ⏭️ | same path as #7 | |
| 9 | ⏭️ | _publish_story uses same MediaRenderer + service.ig_publish_media kind=STORIES | |
| 10 | ⏭️ | mirror of #1 against instagram_oauth cred; backend code identical | |
| 11 | ✅ | DM Test event end-to-end earlier in session (Cell #2 equivalent on child app) | |
| 12 | ⏭️ | mirror of #3 against instagram_oauth | |
| 13 | ⏭️ | mirror of #4 | |
| 14 | ⏭️ | mirror of #5 | |
| 15 | 🔒 | Real comment delivery requires **Advanced Access** on `pages_read_user_content` (Meta gate, not Fuse). Pipeline identical to #1 once approved | confirm post-Live: real comment → workflow → reply action |
| 16 | ✅ | Real Messenger DM from tester delivered → workflow fired → send_message POST 200 (real reply sent) | first true production-shape E2E. Messages on Page object deliver to testers in Dev mode without Live |
| 17 | ⏳ | | |
| 18 | ⏳ | | |
| 19 | ✅ | Get Started tap → postback webhook → reply sent. Fuse auto-installed the button via `register_messenger_get_started` at /listen time | end-to-end with zero manual API setup on the user's side |
| 20 | ⏳ | | |
| 21 | ⏳ | | |
| 22 | ✅ | FB Page post published end-to-end (text + media via 3-tab picker) | required adding `pages_manage_posts` to the FB Login for Business Configuration (not just the app perms page) |
| 23 | ✅/🔒 | Inbound trigger **fires** — real WA message delivered, 1 workflow triggered. Outbound send_text reply gated by error 131031 "Business Account locked" until BV approves the WABA | trigger pipeline fully proven; send_text retry post-BV |
| 24 | 🔒 | Same BV lock | send_template requires approved template + unlocked WABA |
| 25 | 🔒 | Same BV lock | |
| 26 | 🔒 | Status callbacks arrived but classifier maps to `wa.statuses` only when trigger event_type=Status. Plumbing verified | switch event_type to Status to see fire |
| 27 | 🔒 | Same BV lock + filter test | |
| 28 | ⏳ | | |

## After Live mode

Once Business Verification + App Review approves and the app flips to Live, retest every row with **real** events from external tester accounts:

- Real IG message bodies arrive populated (`messaging.text` not `messaging.unknown` / `message_edit`)
- Comments from non-tester accounts deliver
- WhatsApp messages from any number deliver

Document any payload-shape differences against synthetic Test events in the Notes column.

## Known limits in Dev mode

- IG real DMs from testers deliver as `message_edit` envelopes (mid + num_edit only — no text / sender id / recipient id)
- IG comments don't deliver real-time in Dev mode even for testers (`instagram_business_manage_comments` requires Advanced Access)
- WhatsApp real messages need a test WABA + test number registered under the app
- All non-tester traffic blocked until Live

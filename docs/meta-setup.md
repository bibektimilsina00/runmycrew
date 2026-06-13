# Meta Integration — Setup & Test Guide

End-to-end guide to wire up and test the Facebook + Instagram + Messenger + WhatsApp + Lead Ads integration shipped across PRs #96–#101.

If you skip a step here, something downstream will silently break — webhooks won't deliver, OAuth won't redirect, or the resource picker will return an empty list. Read each section in order the first time.

---

## 1. What's shipped

**29 nodes** across 4 Meta product surfaces:

| Surface | Triggers | Actions |
|---|---|---|
| Instagram | `ig_comment`, `ig_mention`, `ig_message`, `ig_story_reply`, `ig_story_mention` | `ig_send_dm`, `ig_reply_comment`, `ig_publish_post`, `ig_publish_story` |
| Facebook Page / Messenger | `fb_message`, `fb_postback`, `fb_comment`, `fb_mention`, `fb_reaction` | `fb_send_message`, `fb_reply_comment`, `fb_publish_post` |
| WhatsApp Cloud API | `wa_message`, `wa_status` | `wa_send_message`, `wa_send_template`, `wa_mark_read` |
| Lead Ads | `lead_submission` | `lead_fetch` |

Plus:
- One unified `meta_oauth` OAuth credential (Phase 1)
- One signed webhook receiver (`POST /api/v1/webhooks/meta/{app_id}`)
- DB-indexed routing via the `metasubscription` table (PR C)
- Auto-subscribe on workflow save via `/{target}/subscribed_apps`
- Frontend `meta-resource` + `wa-template` field types

---

## 2. Prerequisites

| Need | Why |
|---|---|
| Personal Facebook account | OAuth login + admin role for testing |
| One Facebook Page you admin | Required for Page/Messenger/IG/Lead Ads |
| One Instagram Business or Creator account | Required for IG nodes — must be linked to the Page above |
| Public HTTPS endpoint pointing at your local API | Meta refuses `http://` and `localhost` webhooks |
| Postgres + Redis running locally | Standard Fuse dev requirements |
| (Optional) Verified WhatsApp Business Account | Required for WA nodes — separate flow, see §10 |

You **don't** need App Review approval to test. The app stays in Development Mode and works for anyone listed as a Tester (§4).

---

## 3. Local environment setup

### 3.1 Get a public tunnel

Meta hits your webhook endpoint over public HTTPS. Two options:

**Option A — ngrok (recommended)**
```bash
brew install ngrok
ngrok config add-authtoken <your-token>  # free tier signup needed
ngrok http 8000
```
Note the `https://xxxxx.ngrok-free.app` URL. Keep this terminal open the entire session.

**Option B — Cloudflare tunnel (no signup)**
```bash
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://localhost:8000
```

Whichever you pick, copy the public URL. It will be referenced as `${PUBLIC_URL}` below.

### 3.2 Configure env vars

Edit `apps/api/.env` (create from `.env.example` if needed):

```bash
# Required: Meta app credentials (filled in §4)
META_APP_ID=
META_APP_SECRET=

# Required: shared secret for the webhook verification handshake.
# Pick any long random string. Same value goes into Meta's webhook UI in §6.
META_WEBHOOK_VERIFY_TOKEN=replace-this-with-32-random-chars

# Optional: pin Graph API version. Default v20.0 works for everything.
META_GRAPH_API_VERSION=v20.0

# CRITICAL: must match your tunnel host so OAuth redirects land back here
BASE_URL=https://xxxxx.ngrok-free.app
```

Generate a strong verify token:
```bash
openssl rand -hex 32
```

### 3.3 Start services

```bash
# Terminal 1 — Postgres + Redis
docker compose up -d postgres redis

# Terminal 2 — API
cd apps/api
uv run uvicorn apps.api.app.main:app --reload --port 8000

# Terminal 3 — frontend
cd apps/web
pnpm dev
```

### 3.4 Apply migrations

```bash
cd apps/api
PYTHONPATH=$(git rev-parse --show-toplevel) uv run alembic upgrade head
```

This creates the `metasubscription` table introduced in PR C.

---

## 4. Create the Meta Developer App

1. Sign in at https://developers.facebook.com using your personal FB account
2. **My Apps** → **Create App**
3. **Use Case**: pick **Other** → **Next**
4. **App Type**: **Business** → **Next**
5. **App Name**: `Fuse Local Dev` (or any name)
6. **App Contact Email**: yours
7. **Business Portfolio**: pick one or create — required even for personal dev
8. Click **Create App**

You land on the App Dashboard.

### 4.1 Capture App ID + Secret

- **App ID** — visible at the top of the dashboard
- **App Secret** — Settings → Basic → click **Show** → paste your FB password to reveal

Paste both into `apps/api/.env`:
```bash
META_APP_ID=<your-numeric-app-id>
META_APP_SECRET=<your-app-secret-from-meta-dashboard>
```

**Restart the API** so the new env vars load.

### 4.2 Add yourself as a Tester

App Dashboard → **App Roles** → **Roles** → **Add People** → pick **Testers** → enter your own Facebook handle → send invite.

Accept the invite at https://developers.facebook.com/settings/developer/requests/

While the app is in **Development Mode**, OAuth only works for accounts listed here. This is fine for testing.

### 4.3 Configure Basic Settings

Settings → Basic:
- **App Domains**: add your tunnel host without `https://` (e.g. `xxxxx.ngrok-free.app`)
- **Privacy Policy URL**: any URL works for development (`https://example.com/privacy`)
- **Category**: any
- **Save Changes**

---

## 5. Add Products

Left sidebar → **Add Product** — enable these one by one:

| Product | Required for |
|---|---|
| Facebook Login for Business | OAuth (must be installed) |
| Webhooks | Receiving events |
| Instagram | IG nodes |
| WhatsApp | WA nodes (optional, see §10) |

### 5.1 Configure Facebook Login

Facebook Login → **Settings**:
- **Valid OAuth Redirect URIs**:
  ```
  ${PUBLIC_URL}/api/v1/credentials/oauth/meta/callback
  ```
  Replace `${PUBLIC_URL}` with your tunnel URL. Save.
- **Login with the JavaScript SDK**: Off
- **Embedded Browser OAuth Login**: Off

---

## 6. Configure Webhooks

Webhooks is where Meta gets told "deliver these events to my server." You'll add **one subscription per object** you want events from.

### 6.1 Subscribe the `page` object

Webhooks → **Add Subscription** → **Page**:
- **Callback URL**: `${PUBLIC_URL}/api/v1/webhooks/meta/${META_APP_ID}` (literal app id, e.g. `.../webhooks/meta/1234567890123456`)
- **Verify Token**: the same string from `META_WEBHOOK_VERIFY_TOKEN` in your `.env`
- Click **Verify and Save**

If verification fails:
- API isn't running, or tunnel isn't pointing at port 8000
- `META_WEBHOOK_VERIFY_TOKEN` mismatch
- Path uses the App **Secret** instead of the App **ID**

Once verified, click **Edit** on the Page subscription and **toggle** these fields:
- `feed` — Page post comments + reactions
- `mention` — Page mentions
- `messages` — Messenger DMs
- `messaging_postbacks` — button taps / quick replies
- `leadgen` — Lead Ad submissions
- `reactions` (optional — reactions show up under `feed` too)

### 6.2 Subscribe the `instagram` object

Webhooks → **Add Subscription** → **Instagram**:
- Same Callback URL + Verify Token as §6.1
- Verify and Save
- Toggle these fields:
  - `comments`
  - `mentions`
  - `messages` — IG DMs, story replies, story mentions

### 6.3 Subscribe `whatsapp_business_account` (skip if not using WA)

Webhooks → **Add Subscription** → **WhatsApp Business Account**:
- Same Callback URL + Verify Token
- Verify and Save
- Toggle the `messages` field (covers both inbound + status callbacks)

### 6.4 Webhook activity log

Webhooks → **Recent Activity** (per object) shows every delivery + your response code. This is the single most useful debug tool — when something feels broken, check here first.

---

## 7. Connect via OAuth in Fuse

1. Open **`${PUBLIC_URL}`** in your browser (NOT `http://localhost:5173` — Meta enforces the OAuth domain match)
2. Log in to Fuse
3. **Connections** → **New Connection** → search **Meta**
4. You're redirected to Facebook's OAuth dialog
5. Pick the Page(s) + IG account(s) you want to grant access to
6. Approve every permission
7. After approval, you're back in Fuse with a `meta_oauth` credential created

### 7.1 Verify the credential loaded

Check the DB:
```bash
docker compose exec postgres psql -U postgres -d fuse \
  -c "SELECT id, name, type FROM credential WHERE type='meta_oauth';"
```

Then hit the resource discovery endpoint while logged in (browser DevTools Network tab):
```
GET /api/v1/meta/resources?credential_id=<cred-id>&kind=page
GET /api/v1/meta/resources?credential_id=<cred-id>&kind=ig_account
GET /api/v1/meta/resources?credential_id=<cred-id>&kind=waba          # only if WA enabled
GET /api/v1/meta/resources?credential_id=<cred-id>&kind=waba_phone    # only if WA enabled
```

Each should return a non-empty `resources` array. If `page` is empty, you didn't grant Page permissions during OAuth — disconnect and reconnect.

---

## 8. Per-surface test recipes

Run these in order. Each builds confidence in one layer of the stack before the next.

### 8.1 Instagram Comment → DM (comment-to-DM trend)

This is the simplest end-to-end loop. If this works, everything else is just node config.

1. **Skills** → create a new workflow
2. Add a **Instagram Comment** trigger:
   - Meta Account: pick the credential you just made
   - Instagram Account: pick your IG account
   - Post ID: leave blank (fire on all posts)
   - Keyword filter: `GUIDE`
3. Add a **Send Instagram DM** action:
   - Same credential + IG account
   - Recipient IGSID: `{{ $node('Instagram Comment').from_id }}`
   - Message: `Thanks for commenting! Here's the link: https://example.com`
4. Wire trigger → action
5. **Save workflow** + **Activate**

Verify subscription registered:
```sql
SELECT trigger_type, target_id, field, meta_subscribed_at, last_error
FROM metasubscription
WHERE workflow_id = '<your-workflow-id>';
```
- `meta_subscribed_at` should be populated (the auto-subscribe-apps call succeeded)
- `last_error` should be `NULL`

Now trigger:
- On Instagram, from a **different account** (not the connected one), comment `GUIDE` under any of your posts
- Within ~5 seconds the workflow fires
- The commenter receives a DM

If it didn't fire:
- Webhook delivery log shows the event arrived? → if no, Meta isn't routing — recheck §6.2 subscription fields
- Webhook delivery shows 4xx/5xx response from your endpoint? → check API logs for the failure
- 200 response but no workflow ran? → check the `metasubscription` row exists for the workflow + target_id

Note on the 24-hour window: the commenter must have DMed your IG account in the previous 24h for the DM to land. If you're testing with a brand-new account, DM the IG account first, then comment.

### 8.2 Messenger reply bot

1. Trigger: **Messenger DM** → credential + Page
2. Action: **Send Messenger Message**
   - Recipient PSID: `{{ $node('Messenger DM').sender_id }}`
   - Message: `Got your message — we'll be in touch.`
   - Messaging Type: `RESPONSE` (default — valid inside 24h window)
3. From a different FB account, DM your Page
4. Bot replies

To test outside-window sends, change Messaging Type to `MESSAGE_TAG` and pick `HUMAN_AGENT` — that one extends the window to 7 days.

### 8.3 Facebook Page Comment

1. Trigger: **Facebook Comment** → credential + Page
2. Action: **Reply to Facebook Comment** → comment_id from upstream, reply text
3. Comment on a public Page post from another account
4. Workflow fires + reply lands

### 8.4 Facebook Page reaction

1. Trigger: **Facebook Post Reaction** → credential + Page (optionally filter to `LOVE` only)
2. Add any downstream action (e.g. Slack notify via existing Slack node)
3. React to a Page post

### 8.5 Lead Ad submission

Lead Ads requires one extra Meta-side step that **OAuth doesn't automate**:

1. Open your Facebook Page → **Page Settings** → **New Pages Experience** → **Page access** → enable **Lead Access** for your Meta app

Then build the workflow:
1. Trigger: **Lead Ad Submission** → credential + Page (optionally filter by `form_id`)
2. Action: **Fetch Lead Ad Details** → leadgen_id from upstream
3. Test without spending ad money: https://developers.facebook.com/tools/lead-ads-testing/
   - Pick your Page → pick your form → **Send Sample Lead**
4. Workflow fires with `field_data` populated in the action's output

If the fetch returns "Lead Access not granted" — you missed the Page Settings step above.

### 8.6 Instagram publish

1. Action: **Publish Instagram Post**
   - Media Type: `IMAGE`
   - Public Media URL: any reachable public URL (e.g. an S3 presigned URL or a public CDN)
   - Caption: free-form
2. Run the workflow manually
3. Workflow blocks for ~10–30 seconds while Meta processes the media, then publishes

For Reels / video, expect 30–90s processing time. The current implementation polls synchronously — long videos will hit the 60s timeout.

---

## 9. Subscription debugging

The `metasubscription` table is the source of truth for what events route where.

### 9.1 Inspect rows

```sql
SELECT
  ms.trigger_type,
  ms.object_type,
  ms.target_id,
  ms.field,
  ms.is_active,
  ms.meta_subscribed_at,
  ms.last_error,
  w.name as workflow_name
FROM metasubscription ms
JOIN workflow w ON w.id = ms.workflow_id
ORDER BY ms.created_at DESC;
```

What you're looking for:
- `meta_subscribed_at IS NOT NULL` — the `/subscribed_apps` Meta API call succeeded
- `last_error IS NULL` — no Meta-side error
- `is_active = true` — workflow is enabled

### 9.2 Common subscription errors

| `last_error` says... | Fix |
|---|---|
| `subscribed_apps failed: (#10) Application does not have permission for this action` | Permission not granted during OAuth — disconnect + reconnect the credential, picking the Page during the OAuth Pages step |
| `No Page linked to this Instagram account` | The IG account isn't linked to a Page in IG Settings → Account → Linked Accounts |
| `Meta credential not found` | The credential was deleted but the subscription row wasn't — delete the workflow and recreate, or delete the row by hand |
| `No page access token for this target` | Page token expired or revoked — reconnect the credential |

### 9.3 Manual resubscribe

If a Meta-side subscription dropped (page admin revoked, token expired), the workflow's row still routes future events but the Meta dashboard won't fire them. Either:
- Edit the workflow's trigger node and save (re-runs sync, retries subscribe)
- Or in Meta Webhooks → toggle the field off and on

---

## 10. WhatsApp Cloud API (optional — high friction)

WhatsApp has separate Meta-side gates. Budget 1–2 weeks for the gates to clear before you can test the nodes.

### 10.1 Meta-side setup

In https://business.facebook.com → **Settings**:

1. **WhatsApp Accounts** → **Create New** (or attach existing WABA)
2. **Business Verification** — required for production access. Submit company documents. Review takes days to a week.
3. **Phone Numbers** → **Add Number**:
   - Must NOT be registered in the WhatsApp consumer app
   - Verify via SMS/call
4. **Display Name** → submit per number → review takes 24–48h
5. After all approvals, the number is sendable

### 10.2 Templates

Templates are the only way to message users outside the 24h window.

1. **WhatsApp Manager** → **Message Templates** → **Create Template**
2. Pick category: Marketing / Utility / Authentication (pricing differs)
3. Author body with `{{1}}`, `{{2}}` placeholders for variables
4. Submit → review ~24–48h
5. Once APPROVED, the template appears in the `wa_send_template` node's picker

### 10.3 Test the nodes

**Inbound + reply (inside 24h)**:
1. Trigger: **WhatsApp Message** → credential + WABA
2. Action: **Send WhatsApp Message** → reply to `{{ $node('WhatsApp Message').from }}`
3. From a different phone, message your registered WA number
4. Reply lands

**Outside-window (template)**:
1. Action: **Send WhatsApp Template** → pick APPROVED template → fill body variables
2. Trigger via Cron or manual run

**Delivery tracking**:
1. Trigger: **WhatsApp Message Status** → credential + WABA → status filter `delivered`
2. Send a message via §10.3 first
3. Status callbacks fire as the message progresses: `sent` → `delivered` → `read`

---

## 11. Troubleshooting matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| OAuth redirects to a 404 | `BASE_URL` in `.env` doesn't match the tunnel URL | Update + restart API |
| OAuth dialog shows "URL Blocked" | Tunnel URL not in App Domains (Settings → Basic) | Add the tunnel host without `https://` |
| Webhook verification fails | `META_WEBHOOK_VERIFY_TOKEN` mismatch | Re-copy from `.env` into Meta's UI exactly |
| Webhook 401 on POST | Signature verifier rejecting | `META_APP_SECRET` doesn't match Meta's app secret — re-copy from Settings → Basic |
| `/meta/resources?kind=page` returns `[]` | Page permissions not granted during OAuth | Disconnect + reconnect |
| `/meta/resources?kind=ig_account` returns `[]` | IG not linked to any Page you admin | Link in IG Settings → Account → Linked Accounts |
| `/meta/resources?kind=waba` returns `[]` | Business Verification not complete | Wait for verification approval |
| Workflow doesn't fire on Meta event | `metasubscription` row missing OR `meta_subscribed_at IS NULL` | Re-save the workflow (triggers sync) |
| Workflow row exists but event arrives at endpoint as 401 | Signature mismatch (see above) | Re-copy app secret |
| DM 24h-window error | Recipient didn't message you in last 24h | This is Meta's rule, not Fuse's |
| IG publish hangs / 504 | Video too long for the 60s sync timeout | Use a shorter video for now; async worker pattern comes in a later PR |
| Lead fetch returns "Lead Access not granted" | Page admin didn't enable Lead Access for the app | Page Settings → Page access → Lead Access |
| WA send returns error 131047 | Outside 24h window | Use a template (§10.3) |
| `metasubscription.last_error` has Meta error | App permissions issue | Recheck §6 + reconnect credential |

---

## 12. Known limitations

- **App Review required for public launch**: Development Mode works for accounts listed as Testers. Production access (any user can OAuth) needs App Review (1–3 weeks per permission). Not needed for testing.
- **24-hour messaging windows**: enforced by Meta on Messenger, IG DM, and WhatsApp. Outside-window requires Message Tags (Messenger) or Templates (WhatsApp).
- **IG publish is synchronous**: workflow blocks for media processing. Long videos hit the 60s timeout.
- **IG hashtag streams**: capped at 30 unique queries per IG account per 7 days. Don't build "trending hashtag listener" use cases.
- **Cold DMs forbidden**: Meta polices unsolicited outreach. Stick to "reply to people who engaged first" patterns.
- **Lead expiry**: Meta retains leads for 90 days. Pull them fast.
- **Page admin can revoke at any time**: subscriptions go silently dead. The `last_error` field surfaces this once webhook delivery starts failing.

---

## 13. Quick verification checklist

Run through this in order. Each item proves one layer works.

- [ ] Tunnel reachable: `curl https://xxxxx.ngrok-free.app/api/v1/health` returns 200
- [ ] Env vars loaded: API logs show no warnings about Meta on startup
- [ ] Migration applied: `metasubscription` table exists
- [ ] Meta App created, App ID + Secret in `.env`
- [ ] Yourself added as a Tester
- [ ] OAuth redirect URI matches `${PUBLIC_URL}/api/v1/credentials/oauth/meta/callback`
- [ ] Webhook subscriptions verified for `page`, `instagram` (and `whatsapp_business_account` if WA)
- [ ] Fields subscribed per object (§6.1–§6.3)
- [ ] OAuth connect succeeds, credential row in DB
- [ ] `/meta/resources?kind=page` returns Pages
- [ ] `/meta/resources?kind=ig_account` returns IG accounts
- [ ] IG comment-to-DM workflow saved, `metasubscription` row has `meta_subscribed_at IS NOT NULL`
- [ ] Comment fires the workflow + DM lands

Once §8.1 works end-to-end, the rest is node configuration.

# Fuse — Secrets inventory

Where every secret lives, who generates it, and what breaks if it's missing
or rotated.

## Local development

- `.env` at the repo root, copied from `.env.example`.
- Not committed.

## Production

- `deploy/.env` on the VPS (`/opt/fuse/deploy/.env`), copied from
  `deploy/.env.production.example`.
- `chmod 600` so only root can read it.
- Not committed. Pull/push the VPS file manually when you need to share it
  with another operator.

## GitHub Actions

Only one secret is read in CI: `GITHUB_TOKEN` (auto-provided by Actions, no
manual config). It scopes `packages: write` so the workflow can push to
ghcr.io. **No production secrets ever live in GitHub Actions** — CI builds
images; the VPS supplies runtime config.

---

## Secret-by-secret reference

| Var | Generator | Used by | Rotation impact |
|---|---|---|---|
| `SECRET_KEY` | `openssl rand -hex 32` | JWT signing for user sessions | All existing JWTs invalidated — every user is logged out. |
| `ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | Fernet encrypting credential blobs at rest in Postgres | **Existing credentials become un-decryptable**. Rotating means every connection (Google, Meta, Slack, etc) must be re-connected by every user. Treat as forever-immutable in v1; design a key-versioned scheme before changing. |
| `POSTGRES_PASSWORD` | `openssl rand -base64 24 \| tr -d '/+='` | Postgres auth | Compose recreate restarts API + worker (they reload the env). pgdump backups remain readable — they don't store the password. |
| `GOOGLE_CLIENT_ID` / `_SECRET` | Google Cloud Console → OAuth client | Every Google node (gmail, gcal, gdrive, gsheets, gdocs, gtasks, gforms, gpeople, gyt, gslides, gchat, ga4, gsc, gcs) | Rotating breaks new OAuth flows until users reconnect (existing tokens still work until refresh). |
| `META_APP_ID` / `_SECRET` | Meta App Dashboard | Instagram, Facebook, WhatsApp, Lead Ads | Same as Google. |
| OAuth secrets (Slack/GitHub/Notion/Discord/Linear) | Each provider's app dashboard | The corresponding node | Same. |
| AI provider API keys | Each provider's dashboard | LLM, Embeddings, Vision, TTS, STT, Image gen nodes | Workflow runs that use the rotated provider fail until the key is updated. |
| `SMTP_*` | Your SMTP provider (SendGrid / SES / etc) | Workspace invites, password resets | Without SMTP, those emails are logged to stdout instead of sent. |
| `SENTRY_DSN` | sentry.io project | Error tracking on backend + frontend | Optional; missing = no Sentry events emitted. |

---

## Workflow when rotating a secret

1. Generate the new value.
2. Edit `deploy/.env` on the VPS (`fv`, then `nano /opt/fuse/deploy/.env`).
3. `./deploy.sh` — compose picks up env_file changes and restarts the
   services that read it.
4. For OAuth secret rotations: update the OAuth provider console with the
   new secret BEFORE rolling out.

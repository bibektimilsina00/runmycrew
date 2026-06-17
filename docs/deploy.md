# Fuse — Operator runbook

Production deploy on `fuse.bibektimilsina.tech` (DigitalOcean droplet
`139.59.71.226`). Companion to `docs/devops-plan.md`.

Three sections:

- [§1 First-time VPS bootstrap](#1-first-time-vps-bootstrap)
- [§2 Everyday operations](#2-everyday-operations)
- [§3 Incident playbooks](#3-incident-playbooks)

---

## 1. First-time VPS bootstrap

Run once. Takes about 30 minutes.

### 1.1 DNS

On the registrar that owns `bibektimilsina.tech`:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A    | fuse | 139.59.71.226 | 300 |

Wait ~5 minutes, then verify:

```
dig +short fuse.bibektimilsina.tech    # should print 139.59.71.226
```

### 1.2 SSH in

From your laptop:

```
fv                           # uses the alias in ~/.zshrc
```

### 1.3 Install Docker + harden SSH

```
# Docker (official installer; pins repos + signing keys)
curl -fsSL https://get.docker.com | sh

# Confirm
docker --version
docker compose version

# Firewall — SSH + HTTP + HTTPS only
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Recommended: disable password SSH (key-only). Skip if you're still
# bootstrapping access.
# sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
# systemctl restart sshd
```

### 1.4 Clone the repo + drop in secrets

```
mkdir -p /opt/fuse
cd /opt/fuse
git clone https://github.com/bibektimilsina00/fuse_monorepo.git .

cd deploy
cp .env.production.example .env
chmod 600 .env

# Generate the two required secret values:
echo "SECRET_KEY=$(openssl rand -hex 32)"   >> /tmp/fuse-secrets
echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> /tmp/fuse-secrets
echo "POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' )" >> /tmp/fuse-secrets
cat /tmp/fuse-secrets   # paste into .env, then:
shred -u /tmp/fuse-secrets

# Now edit .env and fill the OAuth + AI provider keys you actually use.
nano .env
```

> ⚠️ DO NOT commit `.env`. The `.gitignore` rule covers it; double-check with
> `git status` after editing.

### 1.5 First boot

```
cd /opt/fuse/deploy
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d
docker compose -f docker-compose.production.yml logs -f web api
```

What you should see:

- `db` becomes healthy in ~10 s.
- `api` runs `alembic upgrade head` (logs include `[entrypoint] Migrations done.`).
- `worker` + `beat` start, log `celery@<hostname> ready`.
- `web` (Caddy) requests a Let's Encrypt cert on first HTTPS request. Logs include `certificate obtained successfully`.

Hit:

```
curl -fsS https://fuse.bibektimilsina.tech/api/v1/health
# {"status":"ok"}
```

### 1.6 Make ghcr images public

After the first GitHub Actions run pushes to ghcr, the packages are *private* by default — even in a public repo. The VPS gets a 401 on the next `docker compose pull` unless they're public.

GitHub → your profile → Packages → **fuse-api**:

- Package settings → **Change visibility** → Public

Repeat for `fuse-worker` and `fuse-web`.

### 1.7 Update OAuth redirect URIs

Now that you have HTTPS, every OAuth provider needs the new callback URL. For each provider you actually use:

| Provider | Where to update | URL to add |
|---|---|---|
| Google Cloud | APIs & Services → Credentials → OAuth client → Authorized redirect URIs | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/google/callback` |
| Meta | App Dashboard → Use cases → settings → Valid OAuth Redirect URIs | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/facebook/callback` |
| Slack | api.slack.com/apps → OAuth & Permissions → Redirect URLs | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/slack/callback` |
| GitHub | Settings → Developer settings → OAuth Apps → Authorization callback URL | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/github/callback` |
| Notion | Integration settings → Redirect URIs | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/notion/callback` |
| Discord | Developer Portal → app → OAuth2 → Redirects | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/discord/callback` |
| Linear | Workspace settings → API → Application | `https://fuse.bibektimilsina.tech/api/v1/credentials/oauth/linear/callback` |

> Until you do this, every OAuth flow returns "redirect_uri mismatch".

### 1.8 Smoke test

- Open `https://fuse.bibektimilsina.tech` in a browser → app loads.
- Log in. Create a workspace. Add a Google credential → confirm OAuth bounce works end-to-end. Run a simple workflow.

Done.

---

## 2. Everyday operations

### Deploy

```
git push origin main        # locally → triggers Actions build
fv                          # ssh into VPS
cd /opt/fuse/deploy
./deploy.sh
```

`deploy.sh` does: git pull, image pull, compose up, image prune.

### Tail logs

```
docker compose -f docker-compose.production.yml logs -f api worker
docker compose -f docker-compose.production.yml logs --tail=200 web
```

### Inspect health

```
docker compose -f docker-compose.production.yml ps
```

Expected: every row says `(healthy)`. `Up x minutes` without `(healthy)` is still booting; `unhealthy` is broken.

### Restart one service

```
docker compose -f docker-compose.production.yml restart api
```

### Run an ad-hoc Alembic command

```
docker compose -f docker-compose.production.yml exec api \
  uv run --no-sync alembic -c apps/api/alembic.ini history --verbose
```

### Open a psql shell

```
docker compose -f docker-compose.production.yml exec db \
  psql -U fuse -d fuse
```

### Roll back to a previous build

```
# Find the SHA tag in GitHub → Actions → most recent passing run
echo "FUSE_IMAGE_TAG=sha-abc1234" >> .env   # or edit
./deploy.sh
```

To revert the .env override:

```
# Edit .env, set FUSE_IMAGE_TAG=latest (or delete the line)
./deploy.sh
```

---

## 3. Incident playbooks

### "API is 5xx"

```
# 1. What does the API say?
docker compose -f docker-compose.production.yml logs --tail=200 api

# 2. Is the DB up?
docker compose -f docker-compose.production.yml ps db
docker compose -f docker-compose.production.yml exec db pg_isready -U fuse

# 3. Is Redis up?
docker compose -f docker-compose.production.yml exec redis redis-cli ping

# 4. If migrations failed, the entrypoint log will show it.
docker compose -f docker-compose.production.yml restart api

# 5. Still broken — roll back image tag (see §2 → "Roll back").
```

### "Workflow executions stop firing"

Most likely the polling scheduler (`beat`) crashed:

```
docker compose -f docker-compose.production.yml ps beat
docker compose -f docker-compose.production.yml logs --tail=200 beat
docker compose -f docker-compose.production.yml restart beat
```

If `worker` shows `consumer.Connection.OperationalError`, it's a Redis
issue — restart Redis and the workers.

### "Caddy can't get a certificate"

```
docker compose -f docker-compose.production.yml logs --tail=200 web
```

Common causes:
- DNS isn't pointing at the VPS yet (check `dig +short fuse.bibektimilsina.tech`).
- Port 80 is closed (Let's Encrypt's HTTP-01 challenge needs it open).
- LE rate limit — 5 certs per 7 days per registered domain. Wait or use a staging tier.

### "Disk is full"

```
docker system df         # see what's eating it
docker image prune -af   # nuke dangling + unused images (won't touch running)
docker volume ls         # check pg_backups didn't blow up
ls -lh /var/lib/docker/volumes/fuse_pg_backups/_data | tail
```

If `pg_backups` is huge: edit `deploy/backup.sh` retention from 14 to 7 days, then `restart backup`.

### "Need to restore the DB"

See `deploy/restore.sh`. **Test on a scratch DB first** — never run live without a drill.

```
# List dumps:
ls -lh /var/lib/docker/volumes/fuse_pg_backups/_data

# Restore most recent:
./restore.sh /var/lib/docker/volumes/fuse_pg_backups/_data/latest.dump.gz
```

---

## 4. Off-VPS backups (Phase 1 add-on)

Until set up, the only backup is on the same VPS that holds the live data. Acceptable for testing, *not* for real launch.

Recommended add-on: rsync the `pg_backups` volume to Backblaze B2 (~$0.005/GB/mo) or DO Spaces nightly. Cron entry:

```
# /etc/cron.d/fuse-offsite-backup
30 3 * * * root /usr/local/bin/rclone sync /var/lib/docker/volumes/fuse_pg_backups/_data b2:fuse-backups/$(date -u +\%Y\%m) --quiet
```

(Requires `rclone` configured with B2 credentials. Doc the rclone setup separately when you set this up.)

---

## 5. What lives where

| Thing | Location |
|---|---|
| Compose stack | `/opt/fuse/deploy/docker-compose.production.yml` |
| Secrets | `/opt/fuse/deploy/.env` (chmod 600) |
| Postgres data | volume `fuse_postgres_data` → `/var/lib/docker/volumes/fuse_postgres_data/_data` |
| DB backups | volume `fuse_pg_backups` → `/var/lib/docker/volumes/fuse_pg_backups/_data` |
| Caddy certs | volume `fuse_caddy_data` → `/var/lib/docker/volumes/fuse_caddy_data/_data/caddy/certificates` |
| Repo | `/opt/fuse` (git pull from main) |
| Images | `ghcr.io/bibektimilsina00/fuse-{api,worker,web}:<tag>` |

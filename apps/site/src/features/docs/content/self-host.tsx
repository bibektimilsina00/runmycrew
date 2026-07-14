import Link from 'next/link'
import type { DocContent } from './index'

/**
 * Self-hosting pages. Facts mirror deploy/docker-compose.production.yml and
 * apps/api/app/core/config.py (the pydantic Settings class).
 */
export const SELF_HOST: Record<string, DocContent> = {
  'self-host': {
    toc: [
      { id: 'stack', label: 'The stack' },
      { id: 'requirements', label: 'Requirements' },
      { id: 'quickstart', label: 'Quickstart' },
      { id: 'hosted', label: 'Hosted vs self-hosted' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Self-hosting
        </p>
        <h1>Self-host overview</h1>
        <p className="lead">
          RunMyCrew ships as a Docker Compose stack you can run on a single
          VPS. One command brings up the frontend, API, background workers,
          Postgres, Redis and nightly backups.
        </p>

        <h2 id="stack">The stack</h2>
        <p>
          The production stack (<code>deploy/docker-compose.production.yml</code>)
          pulls pre-built images from GHCR and runs eight services:
        </p>
        <ul>
          <li><strong>web</strong> — Caddy reverse proxy + the React app; terminates TLS and is the only public service (ports 80/443).</li>
          <li><strong>site</strong> — the Next.js marketing site.</li>
          <li><strong>api</strong> — the FastAPI backend (internal :8000).</li>
          <li><strong>worker</strong> — Celery worker that executes workflow runs.</li>
          <li><strong>beat</strong> — Celery beat scheduler for cron triggers (exactly one replica).</li>
          <li><strong>db</strong> — Postgres 15 with pgvector.</li>
          <li><strong>redis</strong> — Celery broker + result backend + cache (AOF persistence).</li>
          <li><strong>backup</strong> — nightly <code>pg_dump</code> with 14-day retention.</li>
        </ul>

        <h2 id="requirements">Requirements</h2>
        <ul>
          <li>A Linux host with Docker + Docker Compose v2.</li>
          <li>~2 vCPU / 4 GB RAM to start; workers scale with run volume.</li>
          <li>A domain (and DNS) for the app and API — Caddy provisions TLS automatically.</li>
        </ul>

        <h2 id="quickstart">Quickstart</h2>
        <pre>
          <code>{`git clone https://github.com/<owner>/runmycrew && cd runmycrew/deploy
cp .env.production.example .env
# fill in secrets (see the Environment reference)
docker compose -f docker-compose.production.yml up -d`}</code>
        </pre>
        <p>
          The <code>deploy/deploy.sh</code> wrapper automates redeploys: git
          pull → <code>docker compose pull</code> → <code>up -d</code> → image
          prune. See <Link href="/docs/docker">Docker compose</Link> for the
          service-by-service breakdown and{' '}
          <Link href="/docs/env">Environment reference</Link> for every
          variable.
        </p>

        <h2 id="hosted">Hosted vs self-hosted</h2>
        <p>
          The hosted product at{' '}
          <a href="https://app.runmycrew.com">app.runmycrew.com</a> is the same
          codebase with managed infra, upgrades and backups. Self-host when you
          need data residency, private networking, or your own model keys —
          everything else is identical.
        </p>
      </>
    ),
  },

  docker: {
    toc: [
      { id: 'files', label: 'Compose files' },
      { id: 'services', label: 'Services & ports' },
      { id: 'up', label: 'Bring it up' },
      { id: 'ops', label: 'Day-2 operations' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Self-hosting
        </p>
        <h1>Docker compose</h1>
        <p className="lead">
          Three compose files ship in the repo. For a real deployment you want
          the production one.
        </p>

        <h2 id="files">Compose files</h2>
        <ul>
          <li><code>deploy/docker-compose.production.yml</code> — the production stack (pulls images, no local build).</li>
          <li><code>docker-compose.yml</code> — local dev (builds api + worker locally; db/redis/api/worker only).</li>
          <li><code>docker-compose.e2e.yml</code> — the end-to-end test stack; not for hosting.</li>
        </ul>

        <h2 id="services">Services &amp; ports</h2>
        <p>
          Only <code>web</code> is published — it fronts everything else on the
          internal Docker network:
        </p>
        <pre>
          <code>{`web     80, 443   Caddy + React app (public, TLS)
site    3100      Next.js marketing (internal)
api     8000      FastAPI (internal)
worker  —         Celery worker (concurrency 2)
beat    —         Celery beat (single replica — never scale >1)
db      5432      Postgres 15 + pgvector (internal)
redis   6379      broker / results / cache (internal)
backup  —         pg_dump loop, 14-day retention`}</code>
        </pre>
        <p>
          The dev compose additionally publishes <code>api:8000</code>,{' '}
          <code>db:5432</code> and <code>redis:6379</code> to localhost for
          debugging.
        </p>

        <h2 id="up">Bring it up</h2>
        <pre>
          <code>{`cd deploy
docker compose -f docker-compose.production.yml up -d
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs -f api`}</code>
        </pre>
        <p>
          Database migrations run automatically on API start. The{' '}
          <code>pg-init/01_extensions.sql</code> script enables{' '}
          <code>pgvector</code> on first boot.
        </p>

        <h2 id="ops">Day-2 operations</h2>
        <ul>
          <li><strong>Update</strong> — <code>./deploy.sh</code> (pull, recreate, prune).</li>
          <li><strong>Scale workers</strong> — <code>docker compose up -d --scale worker=3</code>. Leave <code>beat</code> at 1.</li>
          <li><strong>Backups</strong> — see <Link href="/docs/backup">Backup &amp; restore</Link>.</li>
        </ul>
      </>
    ),
  },

  env: {
    toc: [
      { id: 'model', label: 'How config loads' },
      { id: 'required', label: 'Required secrets' },
      { id: 'core', label: 'Core & URLs' },
      { id: 'data', label: 'Database & Redis' },
      { id: 'email', label: 'Email' },
      { id: 'oauth', label: 'Integration OAuth' },
      { id: 'llm', label: 'Model keys' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Self-hosting
        </p>
        <h1>Environment reference</h1>
        <p className="lead">
          Config is a pydantic <code>Settings</code> class that loads from{' '}
          <code>.env</code>. Start from{' '}
          <code>deploy/.env.production.example</code> and fill the values below.
        </p>

        <h2 id="model">How config loads</h2>
        <p>
          There is <strong>no</strong> <code>DATABASE_URL</code> — the URI is
          computed from the <code>POSTGRES_*</code> parts, and the Celery
          broker/result URLs from <code>REDIS_HOST</code>/<code>REDIS_PORT</code>.
          In <code>production</code> the app refuses to boot if{' '}
          <code>SECRET_KEY</code> or <code>ENCRYPTION_KEY</code> are missing or
          default.
        </p>

        <h2 id="required">Required secrets</h2>
        <pre>
          <code>{`SECRET_KEY=      # JWT signing — openssl rand -hex 32
ENCRYPTION_KEY=  # Fernet key for credential encryption
ENVIRONMENT=production`}</code>
        </pre>

        <h2 id="core">Core &amp; URLs</h2>
        <pre>
          <code>{`BASE_URL=https://api.yourdomain.com
PUBLIC_BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://app.yourdomain.com
PUBLIC_APP_BASE_URL=https://app.yourdomain.com
BACKEND_CORS_ORIGINS=https://app.yourdomain.com
ACCESS_TOKEN_EXPIRE_MINUTES=10080`}</code>
        </pre>

        <h2 id="data">Database &amp; Redis</h2>
        <pre>
          <code>{`POSTGRES_SERVER=db
POSTGRES_USER=runmycrew
POSTGRES_PASSWORD=<strong>
POSTGRES_DB=runmycrew
REDIS_HOST=redis
REDIS_PORT=6379`}</code>
        </pre>

        <h2 id="email">Email</h2>
        <p>
          Optional. Without it, invites and password resets are logged to
          stdout instead of sent. Prefer Resend (HTTP, avoids blocked SMTP
          ports); SMTP is the fallback.
        </p>
        <pre>
          <code>{`RESEND_API_KEY=re_...
# or SMTP:
SMTP_HOST= SMTP_PORT=587 SMTP_USER= SMTP_PASSWORD= SMTP_TLS=true
SMTP_FROM=hello@yourdomain.com
SMTP_FROM_NAME=RunMyCrew`}</code>
        </pre>

        <h2 id="oauth">Integration OAuth</h2>
        <p>
          Each connectable app needs a client id + secret from that provider’s
          developer console (only set the ones you use):
        </p>
        <pre>
          <code>{`GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET
SLACK_CLIENT_ID / SLACK_CLIENT_SECRET
GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET
NOTION_CLIENT_ID / NOTION_CLIENT_SECRET
LINEAR_CLIENT_ID / LINEAR_CLIENT_SECRET
MICROSOFT_CLIENT_ID / MICROSOFT_CLIENT_SECRET
DISCORD_CLIENT_ID / DISCORD_CLIENT_SECRET / DISCORD_BOT_TOKEN
META_APP_ID / META_APP_SECRET / META_WEBHOOK_VERIFY_TOKEN
# + Asana, HubSpot, Calendly, Zoom, Box, Dropbox, DocuSign, LinkedIn`}</code>
        </pre>

        <h2 id="llm">Model keys</h2>
        <p>Bring your own LLM keys — set whichever providers you route to:</p>
        <pre>
          <code>{`ANTHROPIC_API_KEY=   OPENAI_API_KEY=   GEMINI_API_KEY=   GROQ_API_KEY=
# also supported: OpenRouter, DeepSeek, Mistral, xAI, Together, Fireworks, Perplexity`}</code>
        </pre>
      </>
    ),
  },

  backup: {
    toc: [
      { id: 'what', label: 'What is backed up' },
      { id: 'backups', label: 'Automatic backups' },
      { id: 'restore', label: 'Restore' },
      { id: 'offsite', label: 'Offsite copies' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Self-hosting
        </p>
        <h1>Backup &amp; restore</h1>
        <p className="lead">
          Postgres is the single source of truth — everything durable lives
          there. Redis holds only queue and cache state. Back up Postgres and
          you can rebuild the whole stack.
        </p>

        <h2 id="what">What is backed up</h2>
        <p>
          Workflows, runs, connections (encrypted with your{' '}
          <code>ENCRYPTION_KEY</code>), tables, knowledge bases and users all
          live in Postgres. Keep <code>ENCRYPTION_KEY</code> somewhere safe and
          separate — without it, restored credentials can’t be decrypted.
        </p>

        <h2 id="backups">Automatic backups</h2>
        <p>
          The <code>backup</code> service runs on a 24-hour loop:{' '}
          <code>pg_dump --format=custom | gzip</code> into the{' '}
          <code>pg_backups</code> volume, updating a <code>latest.dump.gz</code>{' '}
          symlink and pruning dumps older than 14 days.
        </p>
        <blockquote>
          The loop sleeps 24h from container start, so “nightly” means “every
          24h since the backup container last (re)started,” not a fixed clock
          hour. Restart the container at your preferred time to anchor it.
        </blockquote>

        <h2 id="restore">Restore</h2>
        <p>
          <code>deploy/restore.sh</code> performs a destructive{' '}
          <code>pg_restore</code> from a dump path (or <code>latest.dump.gz</code>):
        </p>
        <pre>
          <code>{`cd deploy
./restore.sh /backups/latest.dump.gz   # DROPS + restores the database`}</code>
        </pre>

        <h2 id="offsite">Offsite copies</h2>
        <p>
          The <code>pg_backups</code> volume lives on the same host — copy it
          somewhere else on a schedule (e.g. <code>rclone</code> to object
          storage) so a lost VPS doesn’t take your backups with it.
        </p>
      </>
    ),
  },
}

# syntax=docker/dockerfile:1.7

# ── Stage 1 ─ build the static React bundle ─────────────────────────────
FROM node:26-alpine AS build

WORKDIR /app

# Enable pnpm via corepack (lockfile-aware).
RUN corepack enable

# Copy the lockfile + workspace manifests first so layer caching survives
# code-only edits — only manifest changes invalidate the install layer.
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/web/package.json ./apps/web/

RUN pnpm install --frozen-lockfile --filter web...

# Now the actual sources.
COPY apps/web ./apps/web

# `vite build` reads VITE_* env vars at build time. Frontend talks to
# `/api/v1` on the same origin (Caddy reverse-proxies), so the default
# baked here is the production value.
ENV VITE_API_URL=/api/v1

WORKDIR /app/apps/web
RUN pnpm build

# ── Stage 2 ─ Caddy serving the static bundle ───────────────────────────
# Single image — no shared volume, no second container coordinating the
# handoff. Web container = Caddy + the React build, period.
FROM caddy:2-alpine

# Drop privileges. Caddy on alpine ships a non-root `caddy` user.
COPY --from=build /app/apps/web/dist /srv
COPY apps/web/Caddyfile /etc/caddy/Caddyfile

EXPOSE 80 443

# `/healthz` is served by Caddy itself (no upstream call) so the
# container's own healthcheck is independent of the API.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --spider -q http://localhost/healthz || exit 1

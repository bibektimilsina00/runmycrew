# syntax=docker/dockerfile:1.7
# ─── Fuse marketing site — Next.js 16 standalone ───────────────────────
#
# Multi-stage build:
#   1. deps:    install pnpm workspace deps for `apps/site` only.
#   2. build:   `pnpm --filter fuse-site build` → produces
#               `apps/site/.next/standalone` + `.next/static` + `public`.
#   3. runtime: copy the three folders into a slim node:22-alpine image
#               and run `node server.js` as a non-root user.
#
# The image is built from the monorepo ROOT (not apps/site) because
# pnpm needs the lockfile + workspace.yaml at that level to resolve.
# ───────────────────────────────────────────────────────────────────────

ARG NODE_VERSION=22.20-alpine

# ─── 1. dependencies ──────────────────────────────────────────────────
FROM node:${NODE_VERSION} AS deps
WORKDIR /repo

# pnpm via corepack so the version matches package.json's packageManager.
RUN corepack enable && corepack prepare pnpm@11.4.0 --activate

# Copy ONLY what's needed to resolve the workspace graph so the Docker
# layer cache survives source-code changes.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
# Node workspace members only — `apps/api` and `apps/worker` are Python
# (no package.json) so pnpm-workspace ignores them at resolve time.
COPY apps/site/package.json apps/site/package.json
COPY apps/web/package.json  apps/web/package.json

RUN pnpm install --frozen-lockfile --filter fuse-site...

# ─── 2. build ─────────────────────────────────────────────────────────
FROM node:${NODE_VERSION} AS build
WORKDIR /repo
RUN corepack enable && corepack prepare pnpm@11.4.0 --activate

# Bring over installed deps + the rest of the source.
COPY --from=deps /repo /repo
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter fuse-site build

# ─── 3. runtime ───────────────────────────────────────────────────────
FROM node:${NODE_VERSION} AS runtime
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3100
ENV HOSTNAME=0.0.0.0

# Non-root for surface reduction.
RUN addgroup -g 10001 -S app && adduser -S -u 10001 -G app app

# Next standalone output ships its own `node_modules`. We only need
# the static + public folders alongside it.
COPY --from=build --chown=app:app /repo/apps/site/.next/standalone ./
COPY --from=build --chown=app:app /repo/apps/site/.next/static ./apps/site/.next/static
COPY --from=build --chown=app:app /repo/apps/site/public ./apps/site/public

USER app
EXPOSE 3100

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --spider -q http://127.0.0.1:3100/ || exit 1

CMD ["node", "apps/site/server.js"]

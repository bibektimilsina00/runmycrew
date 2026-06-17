#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Fuse — VPS deploy
#
# Run from /opt/fuse/deploy:
#     ./deploy.sh                  # update to whatever main currently builds
#     FUSE_IMAGE_TAG=sha-abc1234 ./deploy.sh   # pin a specific build
#
# What it does:
#   1. Fast-forward pull repo (compose YAML + Caddyfile updates).
#   2. Pull newer images from ghcr.io.
#   3. Recreate any service whose image / config changed.
#   4. Prune dangling images so the VPS disk doesn't fill.
# ----------------------------------------------------------------------
set -euo pipefail

cd "$(dirname "$0")"
COMPOSE_FILE="docker-compose.production.yml"

if [[ ! -f .env ]]; then
  echo "✗ deploy/.env is missing — copy from .env.production.example and fill secrets." >&2
  exit 1
fi

echo "▶ Pulling repo for compose + Caddyfile updates…"
git pull --ff-only

echo "▶ Pulling images from ghcr.io…"
docker compose -f "$COMPOSE_FILE" pull

echo "▶ Recreating changed services…"
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

echo "▶ Pruning dangling images…"
docker image prune -f >/dev/null

echo
echo "✓ Fuse updated."
echo "  Repo HEAD: $(git rev-parse --short HEAD)"
echo "  Image tag: ${FUSE_IMAGE_TAG:-latest}"
echo
echo "Tail logs with:"
echo "  docker compose -f $COMPOSE_FILE logs -f web api worker beat"

#!/usr/bin/env bash
# Synthetic hosted-chat probe — exercises api + redis + worker + db in one
# request chain. This is the check that catches the stale-worker class in
# prod (a message that never gets a reply). Wire it into an uptime monitor
# (cron + curl, or a hosted checker hitting a small wrapper) on a 5-min
# cadence and alert on non-zero exit.
#
# Prereq: a dedicated public chat app exists whose graph echoes the input
# (or runs a trivial deterministic node) so the reply is fast and free.
#
# Usage:
#   BASE=https://app.runmycrew.com WS=probe-ws SLUG=probe-chat \
#   TIMEOUT=45 ./scripts/synthetic-chat-probe.sh
#
# Exit 0 = a reply streamed back within TIMEOUT. Non-zero = alert.
set -euo pipefail

BASE="${BASE:?set BASE}"
WS="${WS:?set WS (workspace slug)}"
SLUG="${SLUG:?set SLUG (app slug)}"
TIMEOUT="${TIMEOUT:-45}"
API="${BASE}/api/v1/apps/${WS}/${SLUG}"
JAR="$(mktemp)"
trap 'rm -f "$JAR"' EXIT

fail() { echo "PROBE FAIL: $*" >&2; exit 1; }

# 1. Resolve the app (404 → misconfigured or inactive).
curl -fsS "${API}" -o /dev/null || fail "app did not resolve (${API})"

# 2. Open a session (sets the cookie).
curl -fsS -c "$JAR" -X POST "${API}/session" -H 'content-type: application/json' -d '{}' \
  -o /dev/null || fail "session create failed"

# 3. Send a message, capture the execution id.
SEND=$(curl -fsS -b "$JAR" -c "$JAR" -X POST "${API}/message" \
  -H 'content-type: application/json' -d '{"message":"probe ping"}') \
  || fail "message send failed"
EXEC=$(printf '%s' "$SEND" | sed -n 's/.*"execution_id":"\([^"]*\)".*/\1/p')
[ -n "$EXEC" ] || fail "no execution_id in send response: $SEND"

# 4. Stream until a terminal frame arrives or TIMEOUT elapses.
#    A reply proves the whole chain (worker picked it up, ran, published).
if curl -fsS -b "$JAR" --max-time "$TIMEOUT" "${API}/stream/${EXEC}" \
   | grep -qE 'execution_completed|execution_failed|stream_end'; then
  echo "PROBE OK: reply for ${EXEC}"
  exit 0
fi
fail "no terminal event within ${TIMEOUT}s (worker stalled?)"

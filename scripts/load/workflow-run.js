// k6 load test — editor run endpoint at concurrency.
// Fires POST /workflows/{id}/run repeatedly to find how many concurrent
// runs the worker pool sustains before the queue backs up. Record the
// number in RUNBOOK.md.
//
//   k6 run scripts/load/workflow-run.js -e BASE=https://app.runmycrew.com \
//     -e TOKEN=<jwt> -e WORKFLOW_ID=<uuid> -e WS_ID=<workspace-uuid>
//
// Needs a cheap deterministic workflow (manual trigger → code node) owned
// by the token's user so runs are free and fast.
import http from 'k6/http'
import { check, sleep } from 'k6'

const BASE = __ENV.BASE || 'http://localhost:4700'
const TOKEN = __ENV.TOKEN || ''
const WORKFLOW_ID = __ENV.WORKFLOW_ID || ''
const WS_ID = __ENV.WS_ID || ''

export const options = {
  scenarios: {
    ten_concurrent: {
      executor: 'constant-vus',
      vus: 10,
      duration: '1m',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<2000'],
  },
}

export default function () {
  const res = http.post(
    `${BASE}/api/v1/workflows/${WORKFLOW_ID}/run`,
    '{}',
    {
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${TOKEN}`,
        'x-workspace-id': WS_ID,
      },
    },
  )
  check(res, { 'run accepted': (r) => r.status === 200 || r.status === 201 })
  sleep(1)
}

// k6 load test — public hosted-chat chain (session + message).
// Exercises the api + redis + worker + db path at rising concurrency.
// Goal is not to pass/fail but to FIND THE NUMBER: the concurrency where
// p95 crosses 2s or errors appear. Record it in RUNBOOK.md.
//
//   k6 run scripts/load/hosted-chat.js -e BASE=https://app.runmycrew.com \
//     -e WS=probe-ws -e SLUG=probe-chat
//
// Ramps 5 → 100 VUs. Adjust stages for the target ceiling.
import http from 'k6/http'
import { check, sleep } from 'k6'
import { Trend } from 'k6/metrics'

const BASE = __ENV.BASE || 'http://localhost:4700'
const WS = __ENV.WS || 'probe-ws'
const SLUG = __ENV.SLUG || 'probe-chat'
const API = `${BASE}/api/v1/apps/${WS}/${SLUG}`

const sendLatency = new Trend('send_latency_ms', true)

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: '1m', target: 20 },
    { duration: '1m', target: 50 },
    { duration: '1m', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    // These are the lines we're looking for — k6 flags when crossed.
    http_req_failed: ['rate<0.01'],
    send_latency_ms: ['p(95)<2000'],
  },
}

export default function () {
  const jar = http.cookieJar()

  const sess = http.post(`${API}/session`, '{}', {
    headers: { 'content-type': 'application/json' },
    jar,
  })
  check(sess, { 'session 200': (r) => r.status === 200 })

  const t0 = Date.now()
  const send = http.post(`${API}/message`, JSON.stringify({ message: 'load ping' }), {
    headers: { 'content-type': 'application/json' },
    jar,
  })
  sendLatency.add(Date.now() - t0)
  check(send, { 'message accepted': (r) => r.status === 200 })

  sleep(1)
}

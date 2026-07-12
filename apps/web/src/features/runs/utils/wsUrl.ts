/**
 * Base ws(s):// URL for the API, same-origin in every deployment.
 *
 * vite dev proxies `/ws` and Caddy reverse-proxies it in prod, so the
 * socket must target `window.location.host` — NOT a hardcoded
 * `localhost:8000`. That special case sent the socket to whatever dev API
 * happened to sit on :8000, so live run updates (Logs panel, runs list)
 * silently died on any other localhost-served stack (e2e, previews) and
 * on prod if the API ever moved off the same origin.
 */
export function apiWsBaseUrl(): string {
  const rawApiUrl = import.meta.env.VITE_API_URL || '/api/v1'
  if (rawApiUrl.startsWith('http://') || rawApiUrl.startsWith('https://')) {
    return rawApiUrl.replace(/^http/, 'ws')
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}${rawApiUrl}`
}

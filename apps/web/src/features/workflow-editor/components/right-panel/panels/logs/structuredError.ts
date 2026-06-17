/**
 * Decoder for backend-emitted structured error payloads.
 *
 * The backend (`apps/api/app/node_system/base/errors.py`) serialises a
 * small JSON object behind a sentinel prefix so we don't have to bump
 * the websocket / persistence schema. When the inspector sees a string
 * starting with `__fuse_err_v1__`, it parses the JSON tail and renders
 * a structured card; everything else still renders as a plain string.
 *
 * Any node can opt in — Google, Meta, Slack, custom. The format is
 * deliberately tiny so existing nodes don't need to migrate.
 */

const SENTINEL = '__fuse_err_v1__'

export interface StructuredError {
  /** Short, bold headline — what failed. */
  title: string
  /** 1–2 sentence explanation of *why* it failed. */
  summary: string
  /** Bulleted concrete steps. Each ≤ ~80 chars. */
  actions: string[]
  /** Unmodified upstream error body (API JSON, stack excerpt, …). */
  raw: string
  /** Drives the colour palette on the card. */
  severity: 'error' | 'warning'
}

/**
 * Detect and decode a structured error payload. Returns `null` for
 * anything that isn't a sentinel-prefixed JSON string — caller should
 * fall back to its normal rendering.
 */
export function parseStructuredError(value: unknown): StructuredError | null {
  if (typeof value !== 'string' || !value.startsWith(SENTINEL)) return null
  const jsonText = value.slice(SENTINEL.length)
  try {
    const parsed: unknown = JSON.parse(jsonText)
    if (!parsed || typeof parsed !== 'object') return null
    const obj = parsed as Record<string, unknown>
    const title = typeof obj.title === 'string' ? obj.title : ''
    if (!title) return null
    const summary = typeof obj.summary === 'string' ? obj.summary : ''
    const actions = Array.isArray(obj.actions)
      ? obj.actions.filter((a): a is string => typeof a === 'string')
      : []
    const raw = typeof obj.raw === 'string' ? obj.raw : ''
    const severity = obj.severity === 'warning' ? 'warning' : 'error'
    return { title, summary, actions, raw, severity }
  } catch {
    return null
  }
}

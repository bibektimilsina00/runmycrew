import jsonata from 'jsonata'
import type { NodeProperty, PropertyCondition } from '../types/editorTypes'

/**
 * Runtime-only variable heads. Expressions that reference any of these
 * resolve to `null` at design time (no run data on the canvas), so we
 * skip evaluation entirely and the raw `=…` text shows instead.
 */
const RUNTIME_VAR_REGEX = /\$(step|node|trigger|vars|env|secrets|loop)\b/

/**
 * Best-effort, synchronous design-time evaluation of a `=`-prefixed
 * expression via JSONata. Returns the evaluated value as a display
 * string when fully resolvable without runtime data; returns `null`
 * otherwise so the caller shows the raw `=…` text.
 *
 * Uses `jsonata@^1.8` for its synchronous `evaluate` — v2 made evaluate
 * async-only, which doesn't fit the canvas's sync render path.
 *
 * Bails (returns `null`) when:
 * - the value isn't `=`-prefixed.
 * - the expression mentions a runtime variable (`$step`, `$node`,
 *   `$trigger`, `$vars`, `$env`, `$secrets`, `$loop`).
 * - the expression fails to compile / evaluate.
 * - the result is `null` / `undefined` / a non-primitive (no useful
 *   single-cell display).
 */
function tryResolveDesignTime(value: string): string | null {
  let expr: string | null = null
  const trimmed = value.trim()
  if (trimmed.startsWith('{{') && trimmed.endsWith('}}')) {
    expr = trimmed.slice(2, -2).trim()
  } else if (trimmed.startsWith('=')) {
    // Legacy `=expression` saves still resolve so old graphs render the
    // same way until the user touches them and the editor migrates the
    // value to the new `{{ … }}` shape.
    expr = trimmed.slice(1).trim()
  }
  if (!expr) return null
  if (RUNTIME_VAR_REGEX.test(expr)) return null
  try {
    const result = jsonata(expr).evaluate(null) as unknown
    if (result === undefined || result === null) return null
    if (typeof result === 'object') return null
    if (typeof result === 'number' && !Number.isFinite(result)) return null
    return String(result)
  } catch {
    return null
  }
}

export const getPropValuePreview = (val: unknown, propType: string): string => {
  if (val === undefined || val === null || val === '' || (Array.isArray(val) && val.length === 0)) return '-'
  if (
    typeof val === 'string' &&
    (val.startsWith('=') || (val.trim().startsWith('{{') && val.trim().endsWith('}}')))
  ) {
    const resolved = tryResolveDesignTime(val)
    if (resolved !== null) {
      // Same truncation rule as plain strings so a `{{ $sum(1..1000) }}`
      // doesn't explode the node card.
      return resolved.length > 10 ? `${resolved.substring(0, 10)}…` : resolved
    }
    // Fall through to the raw-text path so the user still sees the
    // expression on the canvas — same as before.
  }
  if (propType === 'boolean') return val ? 'True' : 'False'
  if (propType === 'json' || propType === 'key-value') return '...'
  if ((propType === 'schema' || propType === 'list' || propType === 'file-list') && Array.isArray(val)) return `${val.length} items`
  if (typeof val === 'object') return '...'
  if (typeof val === 'string' && val.length > 10) return `${val.substring(0, 10)}…`
  return String(val)
}

export const getDynamicLabel = (prop: NodeProperty): string => prop.label

function matchesCondition(condition: PropertyCondition, values: Record<string, unknown>): boolean {
  if ('all' in condition) return condition.all.every(c => matchesCondition(c, values))
  if ('any' in condition) return condition.any.some(c => matchesCondition(c, values))
  const current = values[condition.field]
  if (Array.isArray(condition.value)) return condition.value.includes(current)
  return current === condition.value
}

// Single source of truth for property visibility, shared by the canvas node and
// the inspector. A property is shown unless its `condition` is set and doesn't
// match — supporting leaf { field, value } and composite { all | any: [...] }.
export const shouldShowProperty = (
  prop: NodeProperty,
  values: Record<string, unknown>,
): boolean => {
  const { condition } = prop
  if (!condition) return true
  return matchesCondition(condition, values)
}

// Properties shown on the canvas node: never hidden, advanced ones only when
// the node is expanded (data.showAdvanced), and conditional ones only when met.
export const getVisibleNodeProperties = (
  properties: NodeProperty[],
  values: Record<string, unknown>,
  showAdvanced: boolean,
): NodeProperty[] => {
  // Match the inspector: condition evaluation must see each property's
  // `default` when the saved props don't have it yet, otherwise a freshly
  // dropped node hides every default-driven conditional field until the
  // user re-clicks the dropdown.
  const merged: Record<string, unknown> = { ...values }
  for (const p of properties) {
    if (merged[p.name] === undefined && p.default !== undefined) merged[p.name] = p.default
  }
  return properties
    .filter(p => p.visibility !== 'hidden')
    .filter(p => p.mode !== 'advanced' || showAdvanced)
    .filter(p => shouldShowProperty(p, merged))
}

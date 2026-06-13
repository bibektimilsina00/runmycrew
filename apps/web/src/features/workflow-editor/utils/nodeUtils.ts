import type { NodeProperty, PropertyCondition } from '../types/editorTypes'

/**
 * Best-effort, synchronous design-time evaluation of a `=`-prefixed
 * expression. Returns a display string when the expression is fully
 * resolvable without any runtime data; returns `null` otherwise so the
 * caller falls back to showing the raw `=…` text.
 *
 * The canvas preview renders synchronously per re-render, so we can't
 * await `jsonata` (its v2 `evaluate` always returns a Promise). Instead
 * we cover the cases the inspector actually surfaces:
 * - pure arithmetic: `=1+1` → `2`, `=2*3-1` → `5`
 * - `&`-string concat between double-quoted literals: `="a" & "b"` → `ab`
 * - the JSONata standalone-string literal: `="hello"` → `hello`
 *
 * Anything outside this subset (runtime variables, function calls,
 * arrays, predicates) returns `null` and the raw text shows on the card.
 */
function tryResolveDesignTime(value: string): string | null {
  if (!value.startsWith('=')) return null
  const expr = value.slice(1).trim()
  if (!expr) return null

  // String literal: `="hello"` or `="abc"`.
  const literal = expr.match(/^"((?:[^"\\]|\\.)*)"$/)
  if (literal) return literal[1].replace(/\\"/g, '"').replace(/\\\\/g, '\\')

  // String concat between quoted parts: `"a" & "b" & "c"`.
  if (/^\s*"(?:[^"\\]|\\.)*"\s*(?:&\s*"(?:[^"\\]|\\.)*"\s*)+$/.test(expr)) {
    const parts = expr.match(/"((?:[^"\\]|\\.)*)"/g)
    if (parts) {
      const result = parts
        .map(p => p.slice(1, -1).replace(/\\"/g, '"').replace(/\\\\/g, '\\'))
        .join('')
      return result
    }
  }

  // Pure arithmetic: digits, operators, decimal point, parens, whitespace.
  // Function constructor with strict-mode guards is safe given the input
  // character whitelist excludes identifiers and dangerous syntax.
  if (/^[\d+\-*/().\s]+$/.test(expr)) {
    try {
      const result = Function(`"use strict"; return (${expr})`)() as unknown
      if (typeof result === 'number' && Number.isFinite(result)) return String(result)
    } catch {
      // fall through
    }
  }

  return null
}

export const getPropValuePreview = (val: unknown, propType: string): string => {
  if (val === undefined || val === null || val === '' || (Array.isArray(val) && val.length === 0)) return '-'
  if (typeof val === 'string' && val.startsWith('=')) {
    const resolved = tryResolveDesignTime(val)
    if (resolved !== null) {
      // Same truncation rule as plain strings so a `=$sum(1..1000)` doesn't
      // explode the node card.
      return resolved.length > 10 ? `${resolved.substring(0, 10)}…` : resolved
    }
    // Fall through to the raw-text path so the user still sees `=…` on the
    // canvas — same as before.
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
): NodeProperty[] =>
  properties
    .filter(p => p.visibility !== 'hidden')
    .filter(p => p.mode !== 'advanced' || showAdvanced)
    .filter(p => shouldShowProperty(p, values))

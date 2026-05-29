import type { NodeProperty, PropertyCondition } from '../types/editorTypes'

export const getPropValuePreview = (val: unknown, propType: string): string => {
  if (val === undefined || val === null || val === '' || (Array.isArray(val) && val.length === 0)) return '-'
  if (propType === 'boolean') return val ? 'True' : 'False'
  if (propType === 'json' || propType === 'key-value') return '...'
  if ((propType === 'schema' || propType === 'list' || propType === 'file-list') && Array.isArray(val)) return `${val.length} items`
  if (typeof val === 'object') return '...'
  if (typeof val === 'string' && val.length > 10) return `${val.substring(0, 10)}…`
  return String(val)
}

export const getDynamicLabel = (prop: NodeProperty, mode: 'manual' | 'dynamic' = 'manual'): string => {
  if (!prop.loadOptions) return prop.label
  if (mode === 'dynamic') return `Select ${prop.label.replace(/\s+ID$/i, '')}`
  return prop.label
}

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

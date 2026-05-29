import type { NodeProperty } from '../types/editorTypes'

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

export const shouldShowProperty = (
  prop: NodeProperty,
  properties: Record<string, unknown>,
): boolean => {
  if (!prop.condition) return true
  const { field, value } = prop.condition as { field: string; value: unknown }
  const current = properties[field]
  if (Array.isArray(value)) return value.includes(current)
  return current === value
}

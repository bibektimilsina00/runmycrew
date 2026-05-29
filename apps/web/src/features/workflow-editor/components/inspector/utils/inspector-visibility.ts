import type { NodeProperty } from '../../../types/editorTypes'

export interface InspectorPropertyGroup {
  name: string
  properties: NodeProperty[]
}

// Evaluates displayOptions (new) and legacy condition (old) — both supported
export function evaluateDisplayOptions(prop: NodeProperty, values: Record<string, unknown>): boolean {
  // New: displayOptions
  const { displayOptions } = prop
  if (displayOptions) {
    if (displayOptions.show) {
      const allMatch = Object.entries(displayOptions.show).every(([field, allowed]) =>
        allowed.includes(values[field]),
      )
      if (!allMatch) return false
    }
    if (displayOptions.hide) {
      const anyMatch = Object.entries(displayOptions.hide).some(([field, hidden]) =>
        hidden.includes(values[field]),
      )
      if (anyMatch) return false
    }
    return true
  }

  // Legacy: condition
  const condition = prop.condition as { field?: string; value?: unknown } | undefined
  if (condition?.field) {
    const current = values[condition.field]
    if (Array.isArray(condition.value)) return condition.value.includes(current)
    return current === condition.value
  }

  return true
}

// Keep legacy export name for backward compatibility
export const conditionMatches = evaluateDisplayOptions

export function getDefaultPropertyValue(prop: NodeProperty): unknown {
  if (prop.default !== undefined) return prop.default
  switch (prop.type) {
    case 'boolean':       return false
    case 'number':        return 0
    case 'key-value':     return {}
    case 'collection':    return prop.typeOptions?.multipleValues ? [] : {}
    case 'fixed-collection': return {}
    case 'list':
    case 'file-list':
    case 'messages':
    case 'multi-options':
    case 'tool-selector':
    case 'skill-selector': return []
    default:              return ''
  }
}

export function splitPropertyGroups(
  definitionProperties: NodeProperty[],
  properties: Record<string, unknown>,
): { basicGroups: InspectorPropertyGroup[]; advancedGroups: InspectorPropertyGroup[] } {
  const visible = definitionProperties.filter(p =>
    p.visibility !== 'hidden' && p.mode !== 'advanced' && evaluateDisplayOptions(p, properties),
  )
  const advanced = definitionProperties.filter(p =>
    p.visibility !== 'hidden' && p.mode === 'advanced' && evaluateDisplayOptions(p, properties),
  )
  return {
    basicGroups: groupProperties(visible),
    advancedGroups: groupProperties(advanced),
  }
}

function groupProperties(props: NodeProperty[]): InspectorPropertyGroup[] {
  const groups = new Map<string, NodeProperty[]>()
  for (const prop of props) {
    const name = prop.group || 'Settings'
    groups.set(name, [...(groups.get(name) ?? []), prop])
  }
  return Array.from(groups, ([name, properties]) => ({ name, properties }))
}

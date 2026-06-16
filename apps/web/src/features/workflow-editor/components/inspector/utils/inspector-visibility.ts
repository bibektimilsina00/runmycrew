import type { NodeProperty } from '../../../types/editorTypes'
import { shouldShowProperty } from '../../../utils/nodeUtils'

export interface InspectorPropertyGroup {
  name: string
  properties: NodeProperty[]
}

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

/** Build a values dict that falls back to each property's `default` when
 *  the saved props haven't recorded a value yet. Condition evaluation runs
 *  against this so a freshly-dropped node shows its conditional fields
 *  immediately — without it, an `operation: send_email` dropdown would
 *  read as undefined on first paint and every send_email-gated field
 *  would stay hidden until the user clicks the dropdown to "set" it. */
export function valuesWithDefaults(
  definitionProperties: NodeProperty[],
  properties: Record<string, unknown>,
): Record<string, unknown> {
  const merged: Record<string, unknown> = { ...properties }
  for (const p of definitionProperties) {
    if (merged[p.name] !== undefined) continue
    if (p.default !== undefined) merged[p.name] = p.default
  }
  return merged
}

export function splitPropertyGroups(
  definitionProperties: NodeProperty[],
  properties: Record<string, unknown>,
): { basicGroups: InspectorPropertyGroup[]; advancedGroups: InspectorPropertyGroup[] } {
  const merged = valuesWithDefaults(definitionProperties, properties)
  const visible = definitionProperties.filter(p =>
    p.visibility !== 'hidden' && p.mode !== 'advanced' && shouldShowProperty(p, merged),
  )
  const advanced = definitionProperties.filter(p =>
    p.visibility !== 'hidden' && p.mode === 'advanced' && shouldShowProperty(p, merged),
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

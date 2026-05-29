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

export function splitPropertyGroups(
  definitionProperties: NodeProperty[],
  properties: Record<string, unknown>,
): { basicGroups: InspectorPropertyGroup[]; advancedGroups: InspectorPropertyGroup[] } {
  const visible = definitionProperties.filter(p =>
    p.visibility !== 'hidden' && p.mode !== 'advanced' && shouldShowProperty(p, properties),
  )
  const advanced = definitionProperties.filter(p =>
    p.visibility !== 'hidden' && p.mode === 'advanced' && shouldShowProperty(p, properties),
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

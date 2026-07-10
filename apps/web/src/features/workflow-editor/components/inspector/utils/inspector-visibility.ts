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
  const ordered = reorderActionFirst(definitionProperties)
  const visible = ordered.filter(p =>
    p.visibility !== 'hidden' && p.mode !== 'advanced' && shouldShowProperty(p, merged),
  )
  const advanced = ordered.filter(p =>
    p.visibility !== 'hidden' && p.mode === 'advanced' && shouldShowProperty(p, merged),
  )
  return {
    basicGroups: groupProperties(visible),
    advancedGroups: groupProperties(advanced),
  }
}

/**
 * Stable reorder of a node definition's properties for inspector display.
 *
 *   action-ish select (operation / resource / action / method)  →  first
 *   credential field                                            →  next
 *   everything else                                             →  declared order
 *
 * Why this and not "fix every node's property order at definition time"?
 * 31 integration nodes today, and each declares `credential` first
 * because that matches the OAuth-setup mental model. The inspector knows
 * what the *user* should see first (the verb being chosen), which is a
 * presentation concern — exactly the kind of rule CLAUDE.md says belongs
 * in this file rather than in the renderers or per-node definitions.
 *
 * The list of action-ish names is intentionally small and exact. A
 * fuzzy match (e.g. anything ending in "operation") would lift unrelated
 * fields like `cron_expression` or `update_operation_id` up the panel.
 */
const ACTION_FIELD_NAMES = new Set(['operation', 'resource', 'action', 'method'])

function propertyPriority(prop: NodeProperty): number {
  if (prop.type === 'options' && ACTION_FIELD_NAMES.has(prop.name)) return 0
  // A credential whose type depends on another field (e.g. the Agent
  // node's credential keyed off `provider`) must stay AFTER the field
  // that drives it — hoisting it above its driver reads backwards.
  if (prop.type === 'credential' && !prop.credentialTypeByField && !prop.dependsOn) return 1
  return 2
}

function reorderActionFirst(props: NodeProperty[]): NodeProperty[] {
  // Pair with original index so equal-priority items keep their declared
  // order — Array.prototype.sort is stable in modern engines, but doing
  // the pairing makes the contract explicit.
  return props
    .map((prop, index) => ({ prop, index, priority: propertyPriority(prop) }))
    .sort((a, b) => a.priority - b.priority || a.index - b.index)
    .map(({ prop }) => prop)
}

function groupProperties(props: NodeProperty[]): InspectorPropertyGroup[] {
  const groups = new Map<string, NodeProperty[]>()
  for (const prop of props) {
    const name = prop.group || 'Settings'
    groups.set(name, [...(groups.get(name) ?? []), prop])
  }
  return Array.from(groups, ([name, properties]) => ({ name, properties }))
}

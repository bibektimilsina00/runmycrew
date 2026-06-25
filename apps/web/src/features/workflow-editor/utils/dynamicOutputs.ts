import type { Node } from 'reactflow'
import type { NodeDefinition } from '../types/editorTypes'

/**
 * One slot in the "what does this node output" schema, shaped the same
 * way `NodeDefinition.outputsSchema` is — so the two sources are
 * interchangeable at the call site.
 */
export interface OutputField {
  label: string
  type: string
}

/**
 * Resolve a node's effective output schema, instance-first.
 *
 * When the definition declares `dynamicOutputsFrom: "<prop>"`, we read
 * `node.data.properties.<prop>` — a collection of `{name, type}` rows —
 * and project each row into an `OutputField`. That's what surfaces the
 * Start node's user-defined inputs as autocomplete entries and as the
 * upstream tree-view stub, without leaking a `node.type === "..."`
 * check into either consumer.
 *
 * Falls back to the static `outputsSchema` declared on the definition
 * when the instance hasn't populated the dynamic source yet, or when
 * the node simply doesn't opt in. Returns `[]` if neither is set.
 */
export function getOutputsSchema(
  node: Node | null | undefined,
  definition: NodeDefinition | null | undefined,
): OutputField[] {
  if (!definition) return []

  const dynamicProp = definition.dynamicOutputsFrom
  if (dynamicProp && node) {
    const props = (node.data?.properties as Record<string, unknown> | undefined) ?? {}
    const rows = props[dynamicProp]
    if (Array.isArray(rows)) {
      const dynamic: OutputField[] = []
      for (const row of rows) {
        if (!row || typeof row !== 'object') continue
        const r = row as Record<string, unknown>
        const name = typeof r.name === 'string' ? r.name.trim() : ''
        if (!name) continue
        const type = typeof r.type === 'string' && r.type.trim() ? r.type.trim() : 'string'
        dynamic.push({ label: name, type })
      }
      // Only swap to the dynamic schema once the user has actually
      // defined at least one row — falls back to the static fallback
      // otherwise so a brand-new Start node still autocompletes
      // `input_data` until the user customises it.
      if (dynamic.length > 0) return dynamic
    }
  }

  return definition.outputsSchema ?? []
}

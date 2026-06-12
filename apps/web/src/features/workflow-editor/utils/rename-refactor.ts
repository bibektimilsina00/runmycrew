import type { Node } from 'reactflow'

/**
 * Rename-aware rewrites for JSONata expressions that reference a node by
 * label, e.g. `$node('Old')` → `$node('New')`.
 *
 * When the user renames a node, every existing expression in every other
 * node's properties has to be updated atomically — otherwise existing
 * references would silently break the next time the workflow runs.
 *
 * This is the only place that knows the rewrite grammar. Both the store's
 * `renameNode` action and the inspector's label-edit boundary call into it
 * so the semantics are consistent.
 */

/**
 * Matches `$node('Label')` and `$node("Label")` calls. The quote character
 * is captured so the replacement preserves the original style, and escape
 * sequences inside the label body (`\\'` / `\\"`) are handled lazily.
 */
const NODE_CALL = /\$node\(\s*(['"])((?:\\.|(?!\1).)*)\1\s*\)/g

/**
 * Rewrite every `$node('oldLabel')` reference in a single string to
 * `$node('newLabel')`. Strings that are not in expression mode (no leading
 * `=`) are left untouched — the JSONata grammar only applies there.
 */
export function rewriteExpressionLabelsInString(
  source: string,
  oldLabel: string,
  newLabel: string,
): string {
  if (!source.startsWith('=')) return source

  return source.replace(NODE_CALL, (full, quote: string, body: string) => {
    const unescaped = unescapeQuote(body, quote)
    if (unescaped !== oldLabel) return full
    return `$node(${quote}${escapeQuote(newLabel, quote)}${quote})`
  })
}

function unescapeQuote(body: string, quote: string): string {
  return body.replace(new RegExp(`\\\\${quote}`, 'g'), quote).replace(/\\\\/g, '\\')
}

function escapeQuote(label: string, quote: string): string {
  return label.replace(/\\/g, '\\\\').replace(new RegExp(quote, 'g'), `\\${quote}`)
}

/**
 * Walk any property-shaped value (dict / list / string / primitive) and
 * apply `rewriteExpressionLabelsInString` to every nested string. Returns
 * the original reference when nothing changed, so ReactFlow / memoised
 * downstream consumers don't see a spurious update.
 */
export function rewriteExpressionLabels(
  value: unknown,
  oldLabel: string,
  newLabel: string,
): unknown {
  if (typeof value === 'string') {
    return rewriteExpressionLabelsInString(value, oldLabel, newLabel)
  }
  if (Array.isArray(value)) {
    let changed = false
    const out = value.map(v => {
      const next = rewriteExpressionLabels(v, oldLabel, newLabel)
      if (next !== v) changed = true
      return next
    })
    return changed ? out : value
  }
  if (value && typeof value === 'object') {
    let changed = false
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      const next = rewriteExpressionLabels(v, oldLabel, newLabel)
      if (next !== v) changed = true
      out[k] = next
    }
    return changed ? out : value
  }
  return value
}

/**
 * Apply the rename to every node's `data.properties` and to the renamed
 * node's own `data.label`. Returns a fresh nodes array; the input is not
 * mutated.
 */
export function renameNodeInGraph(
  nodes: Node[],
  nodeId: string,
  newLabel: string,
): Node[] {
  const target = nodes.find(n => n.id === nodeId)
  if (!target) return nodes
  const oldLabel = (target.data?.label as string | undefined) ?? ''
  if (oldLabel === newLabel) return nodes

  return nodes.map(node => {
    const props = node.data?.properties as Record<string, unknown> | undefined
    const nextProps =
      oldLabel && props
        ? (rewriteExpressionLabels(props, oldLabel, newLabel) as Record<string, unknown>)
        : props
    if (node.id === nodeId) {
      return {
        ...node,
        data: { ...node.data, label: newLabel, properties: nextProps ?? props },
      }
    }
    if (nextProps === props) return node
    return { ...node, data: { ...node.data, properties: nextProps } }
  })
}

/**
 * Determine whether a proposed label is valid for `nodeId`.
 *
 * Returns the user-facing reason the label is rejected, or `null` when the
 * label is acceptable. Empty / whitespace-only labels are rejected — the
 * raw node id is what the resolver falls back to in that case, and we don't
 * want users entering ambiguous blanks. Duplicate labels are rejected
 * because `$node('X')` must resolve unambiguously to a single node.
 */
export function validateNodeLabel(
  nodeId: string,
  proposed: string,
  nodes: Node[],
): string | null {
  const trimmed = proposed.trim()
  if (!trimmed) return 'Label cannot be empty'

  const conflict = nodes.find(n => {
    if (n.id === nodeId) return false
    const other = (n.data?.label as string | undefined)?.trim()
    return other === trimmed
  })
  if (conflict) return 'Label already used by another node'
  return null
}

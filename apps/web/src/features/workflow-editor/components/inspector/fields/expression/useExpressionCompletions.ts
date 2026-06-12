import { useMemo } from 'react'
import type { Node, Edge } from 'reactflow'
import { useWorkflowEditorStore } from '../../../../stores/workflowEditorStore'
import type { NodeDefinition } from '../../../../types/editorTypes'

/**
 * Completion engine for the JSONata expression editor.
 *
 * The expression editor calls this hook with the current source text and
 * the caret position. The hook parses the text immediately before the
 * caret, decides which "trigger" the user is in (root variable, `$step.`
 * field, `$node(...)` label, `$node('X').` field), and returns the matching
 * completions filtered by whatever prefix the user has already typed.
 *
 * The data source is the workflow editor store — same nodes/edges/defs the
 * Inputs panel already reads — so completions are always in sync with
 * graph state.
 */

export interface Completion {
  /** Display label in the popup. */
  label: string
  /** Substring written into the source when the item is selected. */
  insertText: string
  /** Visual classifier shown as a small badge / icon. */
  kind: 'variable' | 'function' | 'field' | 'node'
  /** Right-aligned type hint or short tag. */
  detail?: string
  /** Longer one-line description rendered under the label. */
  description?: string
}

/**
 * Slice of the source text the caller should overwrite when a completion
 * is accepted. Both indices are absolute offsets into the source string.
 */
export interface ReplaceRange {
  start: number
  end: number
}

export interface CompletionState {
  /** True when the parser found a known trigger at the caret. */
  active: boolean
  /** Substring under the caret being filtered (the prefix). */
  prefix: string
  /** Range to overwrite when the user accepts a completion. */
  replaceRange: ReplaceRange
  /** Completions to render, already filtered by prefix and sorted. */
  completions: Completion[]
}

const EMPTY_STATE: CompletionState = {
  active: false,
  prefix: '',
  replaceRange: { start: 0, end: 0 },
  completions: [],
}

const JSONATA_FUNCTIONS: Completion[] = [
  { label: '$sum', insertText: '$sum(', kind: 'function', detail: 'array → number', description: 'Sum the values of an array.' },
  { label: '$count', insertText: '$count(', kind: 'function', detail: 'array → number', description: 'Count items in an array.' },
  { label: '$length', insertText: '$length(', kind: 'function', detail: 'string | array → number', description: 'Length of a string or array.' },
  { label: '$max', insertText: '$max(', kind: 'function', detail: 'array → number', description: 'Largest value in an array.' },
  { label: '$min', insertText: '$min(', kind: 'function', detail: 'array → number', description: 'Smallest value in an array.' },
  { label: '$average', insertText: '$average(', kind: 'function', detail: 'array → number', description: 'Mean of an array.' },
  { label: '$string', insertText: '$string(', kind: 'function', detail: 'any → string', description: 'Cast to string.' },
  { label: '$number', insertText: '$number(', kind: 'function', detail: 'any → number', description: 'Cast to number.' },
  { label: '$uppercase', insertText: '$uppercase(', kind: 'function', detail: 'string → string', description: 'Uppercase a string.' },
  { label: '$lowercase', insertText: '$lowercase(', kind: 'function', detail: 'string → string', description: 'Lowercase a string.' },
  { label: '$substring', insertText: '$substring(', kind: 'function', detail: 'string,n,m → string', description: 'Slice a substring.' },
  { label: '$contains', insertText: '$contains(', kind: 'function', detail: 'string,pattern → bool', description: 'Test substring or regex match.' },
  { label: '$replace', insertText: '$replace(', kind: 'function', detail: 'string,old,new → string', description: 'Find and replace.' },
  { label: '$split', insertText: '$split(', kind: 'function', detail: 'string,sep → array', description: 'Split string by separator.' },
  { label: '$join', insertText: '$join(', kind: 'function', detail: 'array,sep → string', description: 'Join array items with separator.' },
  { label: '$keys', insertText: '$keys(', kind: 'function', detail: 'object → array', description: 'Keys of an object.' },
  { label: '$exists', insertText: '$exists(', kind: 'function', detail: 'any → bool', description: 'Test whether a path matches.' },
  { label: '$boolean', insertText: '$boolean(', kind: 'function', detail: 'any → bool', description: 'Cast to boolean.' },
  { label: '$not', insertText: '$not(', kind: 'function', detail: 'bool → bool', description: 'Logical negation.' },
  { label: '$now', insertText: '$now()', kind: 'function', detail: '() → string', description: 'Current ISO-8601 timestamp.' },
]

interface Ancestor {
  node: Node
  definition: NodeDefinition | null
  label: string
  distance: number
}

export function useExpressionCompletions(
  expression: string,
  caretIndex: number,
): CompletionState {
  const nodes = useWorkflowEditorStore(s => s.nodes)
  const edges = useWorkflowEditorStore(s => s.edges)
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)
  const selectedNodeId = useWorkflowEditorStore(s => s.selectedNodeId)

  const ancestors = useMemo<Ancestor[]>(() => {
    if (!selectedNodeId) return []
    return collectAncestors(selectedNodeId, nodes, edges, nodeDefinitions)
  }, [selectedNodeId, nodes, edges, nodeDefinitions])

  return useMemo<CompletionState>(() => {
    const before = expression.slice(0, caretIndex)

    const stepField = before.match(/\$step\.([A-Za-z_$][\w$]*)?$/)
    if (stepField) {
      const prefix = stepField[1] ?? ''
      const direct = ancestors.find(a => a.distance === 1) ?? null
      const items = stepFieldCompletions(direct, prefix)
      return {
        active: true,
        prefix,
        replaceRange: { start: caretIndex - prefix.length, end: caretIndex },
        completions: items,
      }
    }

    const nodeField = before.match(/\$node\(\s*['"]([^'"]+)['"]\s*\)\.([A-Za-z_$][\w$]*)?$/)
    if (nodeField) {
      const labelArg = nodeField[1]
      const prefix = nodeField[2] ?? ''
      const target = ancestors.find(a => a.label === labelArg) ?? null
      const items = stepFieldCompletions(target, prefix)
      return {
        active: true,
        prefix,
        replaceRange: { start: caretIndex - prefix.length, end: caretIndex },
        completions: items,
      }
    }

    const nodeArg = before.match(/\$node\(\s*['"]([^'"]*)$/)
    if (nodeArg) {
      const prefix = nodeArg[1] ?? ''
      const items = ancestors
        .filter(a => fuzzy(a.label, prefix))
        .sort((a, b) => a.distance - b.distance)
        .map<Completion>(a => ({
          label: a.label,
          insertText: `${a.label}')`,
          kind: 'node',
          detail: a.distance === 1 ? 'direct' : `${a.distance} hops`,
          description: a.definition?.name,
        }))
      return {
        active: true,
        prefix,
        replaceRange: { start: caretIndex - prefix.length, end: caretIndex },
        completions: items,
      }
    }

    const rootDollar = before.match(/\$([A-Za-z_]\w*)?$/)
    if (rootDollar) {
      const prefix = rootDollar[0]
      const items = rootCompletions(prefix, ancestors)
      return {
        active: true,
        prefix,
        replaceRange: { start: caretIndex - prefix.length, end: caretIndex },
        completions: items,
      }
    }

    return EMPTY_STATE
  }, [expression, caretIndex, ancestors])
}

function rootCompletions(prefix: string, ancestors: Ancestor[]): Completion[] {
  const direct = ancestors.find(a => a.distance === 1) ?? null
  const items: Completion[] = []

  if (direct) {
    items.push({
      label: '$step',
      insertText: '$step.',
      kind: 'variable',
      detail: `→ ${direct.label}`,
      description: 'Immediate upstream item.',
    })
  }
  if (ancestors.length > 0) {
    items.push({
      label: '$node',
      insertText: "$node('",
      kind: 'function',
      detail: 'label → item',
      description: 'Reference any upstream node by label.',
    })
  }
  for (const fn of JSONATA_FUNCTIONS) {
    items.push(fn)
  }
  return items.filter(c => fuzzy(c.label, prefix))
}

function stepFieldCompletions(target: Ancestor | null, prefix: string): Completion[] {
  if (!target) return []
  const schema = target.definition?.outputsSchema ?? []
  return schema
    .filter(f => fuzzy(f.label, prefix))
    .map<Completion>(f => ({
      label: f.label,
      insertText: f.label,
      kind: 'field',
      detail: f.type,
      description: `${target.label} → ${f.label}`,
    }))
}

function fuzzy(candidate: string, prefix: string): boolean {
  if (!prefix) return true
  // Both sides can carry a leading `$` (root completions are `$step`,
  // `$node`, `$sum`…); strip it on both before comparing so `$st` matches
  // `$step` and a plain field name like `status_code` still matches `stat`.
  const c = candidate.toLowerCase().replace(/^\$/, '')
  const p = prefix.toLowerCase().replace(/^\$/, '')
  return c.startsWith(p)
}

/**
 * BFS over reverse edges from the given start node. Returns every ancestor
 * with its distance, label, and definition (for outputsSchema lookups).
 * Closest-first; shortest distance wins on multi-path.
 */
function collectAncestors(
  start: string,
  nodes: Node[],
  edges: Edge[],
  defs: NodeDefinition[],
): Ancestor[] {
  const parentsOf = new Map<string, string[]>()
  for (const e of edges) {
    const list = parentsOf.get(e.target)
    if (list) list.push(e.source)
    else parentsOf.set(e.target, [e.source])
  }
  const distance = new Map<string, number>()
  const queue: Array<[string, number]> = [[start, 0]]
  while (queue.length) {
    const [id, d] = queue.shift()!
    for (const src of parentsOf.get(id) ?? []) {
      if (distance.has(src) || src === start) continue
      distance.set(src, d + 1)
      queue.push([src, d + 1])
    }
  }
  const result: Ancestor[] = []
  for (const [id, d] of distance) {
    const node = nodes.find(n => n.id === id)
    if (!node) continue
    const definition = defs.find(def => def.type === node.type) ?? null
    const label = (node.data?.label as string | undefined) || definition?.name || id
    result.push({ node, definition, label, distance: d })
  }
  result.sort((a, b) => a.distance - b.distance)
  return result
}

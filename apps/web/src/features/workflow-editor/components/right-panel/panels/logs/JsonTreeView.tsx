import { useCallback, useMemo, useState } from 'react'
import { ChevronDown, GripVertical } from 'lucide-react'
import { cn } from '@/lib/cn'

interface Props {
  value: unknown
  /** Auto-expand all branches up to this depth on first render. */
  initialDepth?: number
  /** When set, rows are draggable; dropping them on a text field in the
   *  inspector inserts the `{{nodeId.path}}` expression at the cursor. */
  nodeId?: string | null
}

type ValueKind = 'object' | 'array' | 'string' | 'number' | 'boolean' | 'null' | 'undefined' | 'other'

/**
 * Structured tree view of any JSON-shaped value — no raw JSON syntax.
 *
 * Every row shares the same shape: `[key] [type-badge] [meta] [chevron]`.
 * Click the row (or chevron) to toggle the body, which renders nested
 * entries indented behind a vertical guide line. Primitives render their
 * formatted value inside the same indented block, so the structure stays
 * consistent at every depth.
 *
 * When `nodeId` is set, each non-root row is draggable. The drag payload is
 * the interpolation template `{{nodeId.path}}` placed on `text/plain`, so
 * the browser auto-inserts it at the cursor when dropped on any `<input>`
 * or `<textarea>` in the inspector.
 */
export function JsonTreeView({ value, initialDepth = 2, nodeId = null }: Props) {
  const kind = classify(value)

  // Skip the synthetic "root" row — render the value's contents directly.
  // For containers, that means iterating top-level entries inline; for
  // primitives, that means rendering the formatted value alone.
  if (kind === 'object' || kind === 'array') {
    const entries: [string | number, unknown][] =
      kind === 'object'
        ? Object.entries(value as Record<string, unknown>)
        : (value as unknown[]).map((v, i) => [i, v])

    if (entries.length === 0) {
      return (
        <div className="text-[12.5px] leading-[20px] italic text-[var(--text-faint)]">
          {kind === 'object' ? '{}' : '[]'}
        </div>
      )
    }

    return (
      <div className="flex flex-col text-[12.5px] leading-[20px]">
        {entries.map(([k, v]) => (
          <TreeNode
            key={k}
            keyName={k}
            value={v}
            depth={0}
            initialDepth={initialDepth}
            nodeId={nodeId}
            parentPath=""
          />
        ))}
      </div>
    )
  }

  return (
    <div className="text-[12.5px] leading-[20px]">
      <PrimitiveValue value={value} kind={kind} />
    </div>
  )
}

interface NodeProps {
  keyName: string | number | null
  value: unknown
  depth: number
  initialDepth: number
  nodeId: string | null
  parentPath: string
}

/** Build the dot/bracket path for this row given its key and parent path. */
function buildPath(parentPath: string, keyName: string | number | null): string {
  if (keyName === null) return parentPath
  if (typeof keyName === 'number') return `${parentPath}[${keyName}]`
  // Bracket-quote keys that aren't safe dot identifiers.
  const safeIdent = /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(keyName)
  if (!safeIdent) return `${parentPath}[${JSON.stringify(keyName)}]`
  return parentPath ? `${parentPath}.${keyName}` : keyName
}

function TreeNode({ keyName, value, depth, initialDepth, nodeId, parentPath }: NodeProps) {
  const kind = classify(value)
  const [expanded, setExpanded] = useState(depth < initialDepth)
  const toggle = useCallback(() => setExpanded((v) => !v), [])

  const path = buildPath(parentPath, keyName)
  const expression = nodeId && path ? `{{${nodeId}.${path}}}` : null

  const entries = useMemo<[string | number, unknown][]>(() => {
    if (kind === 'object') return Object.entries(value as Record<string, unknown>)
    if (kind === 'array') return (value as unknown[]).map((v, i) => [i, v])
    return []
  }, [kind, value])

  const meta = useMemo<string | null>(() => {
    if (kind === 'object') return `${entries.length} ${entries.length === 1 ? 'key' : 'keys'}`
    if (kind === 'array')  return `${entries.length} ${entries.length === 1 ? 'item' : 'items'}`
    return null
  }, [kind, entries.length])

  return (
    <div className="flex flex-col">
      <Row
        keyName={keyName}
        kind={kind}
        meta={meta}
        expanded={expanded}
        onToggle={toggle}
        expression={expression}
      />
      {expanded && (
        <div className="ml-[10px] border-l border-[var(--border-faint)] pl-3">
          {kind === 'object' || kind === 'array' ? (
            entries.map(([k, v]) => (
              <TreeNode
                key={k}
                keyName={k}
                value={v}
                depth={depth + 1}
                initialDepth={initialDepth}
                nodeId={nodeId}
                parentPath={path}
              />
            ))
          ) : (
            <PrimitiveValue value={value} kind={kind} />
          )}
        </div>
      )}
    </div>
  )
}

interface RowProps {
  keyName: string | number | null
  kind: ValueKind
  meta: string | null
  expanded: boolean
  onToggle: () => void
  expression: string | null
}

function Row({ keyName, kind, meta, expanded, onToggle, expression }: RowProps) {
  const draggable = !!expression

  const handleDragStart = (e: React.DragEvent<HTMLButtonElement>) => {
    if (!expression) return
    // `text/plain` is what browser-native text inputs paste on drop, so we
    // don't need bespoke drop handlers on every field renderer.
    e.dataTransfer.setData('text/plain', expression)
    // Custom MIME for inspector-side type checks (future use).
    e.dataTransfer.setData('application/x-fuse-expression', expression)
    e.dataTransfer.effectAllowed = 'copy'
  }

  return (
    <button
      type="button"
      onClick={onToggle}
      draggable={draggable}
      onDragStart={handleDragStart}
      title={expression ?? undefined}
      className={cn(
        'group flex w-full items-center gap-2 rounded-[5px] py-[3px] pr-1.5 text-left transition-colors hover:bg-[var(--surface)]',
        draggable && 'cursor-grab active:cursor-grabbing',
      )}
    >
      <ChevronDown
        className={cn(
          'h-3 w-3 shrink-0 text-[var(--text-faint)] transition-transform duration-100 group-hover:text-[var(--text-mute)]',
          !expanded && '-rotate-90',
        )}
      />
      <KeyLabel keyName={keyName} />
      <TypeBadge kind={kind} />
      {meta && <span className="text-[11px] text-[var(--text-faint)]">{meta}</span>}
      {draggable && (
        <GripVertical
          className="ml-auto h-3 w-3 shrink-0 text-[var(--text-dim)] opacity-0 transition-opacity group-hover:opacity-100"
          aria-hidden
        />
      )}
    </button>
  )
}

function KeyLabel({ keyName }: { keyName: string | number | null }) {
  if (keyName === null) {
    return <span className="font-semibold text-[var(--text)]">root</span>
  }
  if (typeof keyName === 'number') {
    return (
      <span className="font-mono text-[12px] font-semibold text-[var(--text-mute)] tabular-nums">
        {keyName}
      </span>
    )
  }
  return (
    <span className="truncate text-[12.5px] font-semibold text-[var(--text)]" title={keyName}>
      {keyName}
    </span>
  )
}

// ── Type badge ───────────────────────────────────────────────────────────────

const BADGE_LABEL: Record<ValueKind, string> = {
  object:    'object',
  array:     'array',
  string:    'string',
  number:    'number',
  boolean:   'boolean',
  null:      'null',
  undefined: 'undefined',
  other:     'other',
}

const BADGE_CLASS: Record<ValueKind, string> = {
  object:    'bg-[rgba(125,207,255,0.14)] text-[#7dcfff]',
  array:     'bg-[rgba(187,154,247,0.16)] text-[#bb9af7]',
  string:    'bg-[rgba(158,206,106,0.16)] text-[#9ece6a]',
  number:    'bg-[rgba(224,175,104,0.16)] text-[#e0af68]',
  boolean:   'bg-[rgba(122,162,247,0.16)] text-[#7aa2f7]',
  null:      'bg-[var(--surface-2)] text-[var(--text-mute)]',
  undefined: 'bg-[var(--surface-2)] text-[var(--text-mute)]',
  other:     'bg-[var(--surface-2)] text-[var(--text-mute)]',
}

function TypeBadge({ kind }: { kind: ValueKind }) {
  return (
    <span
      className={cn(
        'shrink-0 rounded-[5px] px-[6px] py-[1px] text-[10.5px] font-medium leading-[14px]',
        BADGE_CLASS[kind],
      )}
    >
      {BADGE_LABEL[kind]}
    </span>
  )
}

// ── Primitive value renderer ──────────────────────────────────────────────────

function PrimitiveValue({ value, kind }: { value: unknown; kind: ValueKind }) {
  return (
    <div className="py-[3px]">
      <PrimitiveText value={value} kind={kind} />
    </div>
  )
}

function PrimitiveText({ value, kind }: { value: unknown; kind: ValueKind }) {
  if (kind === 'string') {
    const text = String(value)
    return (
      <span className="break-all text-[#9ece6a]">
        {text === '' ? <span className="italic opacity-60">""</span> : `"${text}"`}
      </span>
    )
  }
  if (kind === 'number') return <span className="text-[#e0af68] tabular-nums">{String(value)}</span>
  if (kind === 'boolean') return <span className="text-[#7aa2f7]">{value ? 'true' : 'false'}</span>
  if (kind === 'null') return <span className="italic text-[var(--text-mute)]">null</span>
  if (kind === 'undefined') return <span className="italic text-[var(--text-mute)]">undefined</span>
  return <span className="text-[var(--text-mute)]">{String(value)}</span>
}

// ── Classification ────────────────────────────────────────────────────────────

function classify(v: unknown): ValueKind {
  if (v === null) return 'null'
  if (v === undefined) return 'undefined'
  if (Array.isArray(v)) return 'array'
  if (typeof v === 'object') return 'object'
  if (typeof v === 'string') return 'string'
  if (typeof v === 'number') return 'number'
  if (typeof v === 'boolean') return 'boolean'
  return 'other'
}

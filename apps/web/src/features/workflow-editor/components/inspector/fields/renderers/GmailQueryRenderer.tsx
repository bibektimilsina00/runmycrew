import { useEffect, useRef, useState } from 'react'
import type { RendererProps } from '../types'
import { Input } from '@/shared/components'
import { Dropdown, DropdownTrigger, DropdownContent, DropdownItem } from '@/shared/components/Dropdown'
import { ExpressionEditor } from '../expression/ExpressionEditor'
import { cn } from '@/lib/cn'

/**
 * Visual builder for Gmail's search-query syntax. Reads/writes a raw
 * Gmail query string so the backend stays untouched: parses the string
 * into structured chips, lets the user edit them, then serialises
 * back. Free words live in a trailing text input; "Raw" mode drops to
 * the standard expression editor for power users.
 */

type Op =
  | 'from' | 'to' | 'cc' | 'bcc' | 'subject' | 'label' | 'filename'
  | 'is' | 'has' | 'category'
  | 'after' | 'before' | 'older_than' | 'newer_than'
  | 'larger' | 'smaller'

type OperatorDef = {
  op: Op
  label: string
  kind: 'text' | 'preset' | 'date'
  options?: readonly string[]
  placeholder?: string
}

const OPERATORS: readonly OperatorDef[] = [
  { op: 'from',       label: 'From',         kind: 'text',   placeholder: 'sender@example.com' },
  { op: 'to',         label: 'To',           kind: 'text',   placeholder: 'recipient@example.com' },
  { op: 'cc',         label: 'CC',           kind: 'text',   placeholder: 'cc@example.com' },
  { op: 'bcc',        label: 'BCC',          kind: 'text',   placeholder: 'bcc@example.com' },
  { op: 'subject',    label: 'Subject',      kind: 'text',   placeholder: 'word or "exact phrase"' },
  { op: 'label',      label: 'Label',        kind: 'text',   placeholder: 'inbox' },
  { op: 'filename',   label: 'Filename',     kind: 'text',   placeholder: 'report.pdf' },
  { op: 'is',         label: 'Is',           kind: 'preset', options: ['unread','read','starred','important','snoozed'] },
  { op: 'has',        label: 'Has',          kind: 'preset', options: ['attachment','drive','document','spreadsheet','presentation','image','youtube'] },
  { op: 'category',   label: 'Category',     kind: 'preset', options: ['primary','social','promotions','updates','forums'] },
  { op: 'after',      label: 'After',        kind: 'date' },
  { op: 'before',     label: 'Before',       kind: 'date' },
  { op: 'older_than', label: 'Older than',   kind: 'text',   placeholder: '7d / 1m / 1y' },
  { op: 'newer_than', label: 'Newer than',   kind: 'text',   placeholder: '7d / 1m / 1y' },
  { op: 'larger',     label: 'Larger than',  kind: 'text',   placeholder: '1M / 500K' },
  { op: 'smaller',    label: 'Smaller than', kind: 'text',   placeholder: '1M / 500K' },
] as const

const OP_DEFS = new Map(OPERATORS.map(o => [o.op, o]))

type ChipToken  = { kind: 'op'; op: Op; value: string; negated: boolean }
type TextToken  = { kind: 'text'; text: string }
type Token      = ChipToken | TextToken
type ParsedQuery = { chips: ChipToken[]; text: string }

/** Tokenize a Gmail query while respecting quoted values and negation. */
function parseQuery(s: string): ParsedQuery {
  const chips: ChipToken[] = []
  const words: string[] = []
  if (!s) return { chips, text: '' }
  // Match: optional `-`, then either op:"quoted", op:bare, "free quoted",
  // or a single non-whitespace word.
  const re = /(-?)([a-zA-Z_]+):"([^"]*)"|(-?)([a-zA-Z_]+):(\S+)|"([^"]+)"|(\S+)/g
  let m: RegExpExecArray | null
  while ((m = re.exec(s)) !== null) {
    const negQuoted   = m[1]
    const opQuoted    = m[2]
    const valQuoted   = m[3]
    const negBare     = m[4]
    const opBare      = m[5]
    const valBare     = m[6]
    const phrase      = m[7]
    const bareWord    = m[8]
    if (opQuoted && OP_DEFS.has(opQuoted.toLowerCase() as Op)) {
      chips.push({ kind: 'op', op: opQuoted.toLowerCase() as Op, value: valQuoted ?? '', negated: negQuoted === '-' })
    } else if (opBare && OP_DEFS.has(opBare.toLowerCase() as Op)) {
      chips.push({ kind: 'op', op: opBare.toLowerCase() as Op, value: valBare ?? '', negated: negBare === '-' })
    } else if (phrase !== undefined) {
      words.push(`"${phrase}"`)
    } else if (bareWord !== undefined) {
      words.push(bareWord)
    }
  }
  return { chips, text: words.join(' ') }
}

function serializeChip(c: ChipToken): string {
  const v = c.value.trim()
  if (!v) return ''
  const needsQuotes = /\s/.test(v) && !(v.startsWith('"') && v.endsWith('"'))
  const quoted = needsQuotes ? `"${v}"` : v
  return `${c.negated ? '-' : ''}${c.op}:${quoted}`
}

function serialize(q: ParsedQuery): string {
  const chipStr = q.chips.map(serializeChip).filter(Boolean).join(' ')
  const text = q.text.trim()
  return [chipStr, text].filter(Boolean).join(' ')
}

export function GmailQueryRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const raw = value === undefined || value === null ? '' : String(value)
  const [mode, setMode] = useState<'visual' | 'raw'>('visual')

  // We are the source of truth for the parsed shape while the user edits;
  // `raw` is re-parsed only on outside changes (history undo, etc).
  const lastEmitted = useRef(raw)
  const [parsed, setParsed] = useState<ParsedQuery>(() => parseQuery(raw))
  useEffect(() => {
    if (raw !== lastEmitted.current) {
      setParsed(parseQuery(raw))
      lastEmitted.current = raw
    }
  }, [raw])

  const emit = (next: ParsedQuery) => {
    setParsed(next)
    const out = serialize(next)
    lastEmitted.current = out
    onChange(out)
  }

  const updateChip = (idx: number, patch: Partial<ChipToken>) => {
    emit({ ...parsed, chips: parsed.chips.map((c, i) => i === idx ? { ...c, ...patch } : c) })
  }
  const removeChip = (idx: number) => {
    emit({ ...parsed, chips: parsed.chips.filter((_, i) => i !== idx) })
  }
  const addChip = (op: Op) => {
    const def = OP_DEFS.get(op)!
    const initial = def.kind === 'preset' ? (def.options?.[0] ?? '') : ''
    emit({ ...parsed, chips: [...parsed.chips, { kind: 'op', op, value: initial, negated: false }] })
  }

  // Raw mode delegates to the standard expression editor so users keep
  // autocomplete + `{{ }}` interpolation when they need full control.
  if (mode === 'raw') {
    return (
      <div className="space-y-2">
        <div className="flex justify-end">
          <ModeToggle mode={mode} setMode={setMode} disabled={disabled} />
        </div>
        <ExpressionEditor
          value={raw}
          onChange={(v) => { lastEmitted.current = v; onChange(v) }}
          placeholder={prop.placeholder}
          disabled={disabled}
        />
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <ModeToggle mode={mode} setMode={setMode} disabled={disabled} />
      </div>
      <div className={cn(
        'flex flex-wrap items-center gap-1.5',
        'min-h-[42px] px-2 py-2 rounded-[5px]',
        'bg-bg border border-border-faint',
        'hover:border-border-soft focus-within:border-border focus-within:bg-surface',
      )}>
        {parsed.chips.map((chip, i) => (
          <ChipEditor
            key={i}
            chip={chip}
            disabled={disabled}
            onChange={(patch) => updateChip(i, patch)}
            onRemove={() => removeChip(i)}
          />
        ))}
        <Input
          value={parsed.text}
          onChange={(e) => emit({ ...parsed, text: e.target.value })}
          placeholder={parsed.chips.length === 0 ? (prop.placeholder ?? 'Search words…') : 'more words…'}
          disabled={disabled}
          className="!h-7 !py-0 !px-2 !text-xs flex-1 min-w-[120px] !bg-transparent !border-0 focus:!ring-0 focus:!shadow-none"
        />
        <AddFilterButton disabled={disabled} onPick={addChip} />
      </div>
      {prop.description && (
        <p className="text-[11px] text-text-muted">{prop.description}</p>
      )}
    </div>
  )
}

// ── chip editor ──────────────────────────────────────────────────────────

function ChipEditor({
  chip, disabled, onChange, onRemove,
}: {
  chip: ChipToken
  disabled?: boolean
  onChange: (patch: Partial<ChipToken>) => void
  onRemove: () => void
}) {
  const def = OP_DEFS.get(chip.op)!
  const [editing, setEditing] = useState(chip.value === '' && def.kind !== 'preset')
  const inputRef = useRef<HTMLInputElement>(null)
  useEffect(() => { if (editing) inputRef.current?.focus() }, [editing])

  const commit = () => setEditing(false)
  const toggleNegate = () => onChange({ negated: !chip.negated })

  const valueLabel = chip.value || <span className="italic opacity-60">empty</span>

  return (
    <div className={cn(
      'inline-flex items-center gap-1 h-7 rounded-full text-xs',
      'border transition-colors',
      chip.negated
        ? 'border-[var(--danger,#dc2626)]/40 bg-[var(--danger,#dc2626)]/10'
        : 'border-border bg-surface-2',
    )}>
      <button
        type="button"
        onClick={toggleNegate}
        disabled={disabled}
        title={chip.negated ? 'Match messages with this (remove −)' : 'Exclude messages with this (add −)'}
        className={cn(
          'pl-2 pr-0.5 font-mono leading-none',
          chip.negated ? 'text-[var(--danger,#dc2626)]' : 'text-text-muted hover:text-text',
        )}
      >
        {chip.negated ? '−' : ''}
      </button>
      <span className="text-text-muted">{def.label}:</span>
      {def.kind === 'preset' ? (
        <select
          value={chip.value}
          onChange={(e) => onChange({ value: e.target.value })}
          disabled={disabled}
          className="bg-transparent text-text text-xs outline-none border-0 py-0 pr-1 pl-0.5 cursor-pointer"
        >
          {!chip.value && <option value="">—</option>}
          {def.options!.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : editing ? (
        <input
          ref={inputRef}
          type={def.kind === 'date' ? 'date' : 'text'}
          value={def.kind === 'date' ? toIsoDate(chip.value) : chip.value}
          onChange={(e) => onChange({ value: def.kind === 'date' ? fromIsoDate(e.target.value) : e.target.value })}
          onBlur={commit}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === 'Escape') { e.preventDefault(); commit() } }}
          placeholder={def.placeholder}
          disabled={disabled}
          className="bg-transparent text-text text-xs outline-none border-0 py-0 px-1 min-w-[60px] w-[var(--w,auto)]"
          style={{ width: `${Math.max((chip.value?.length ?? 0) + 1, def.placeholder?.length ?? 8)}ch` }}
        />
      ) : (
        <button
          type="button"
          onClick={() => setEditing(true)}
          disabled={disabled}
          className="text-text px-1 hover:underline"
        >
          {valueLabel}
        </button>
      )}
      <button
        type="button"
        onClick={onRemove}
        disabled={disabled}
        title="Remove filter"
        className="px-1.5 text-text-muted hover:text-text leading-none"
      >
        ×
      </button>
    </div>
  )
}

// Gmail accepts `YYYY/MM/DD` for after/before. `<input type="date">`
// emits ISO `YYYY-MM-DD`; convert both directions so the saved string
// stays in Gmail's native format and round-trips on next parse.
function toIsoDate(v: string): string {
  const m = v.match(/^(\d{4})\/(\d{2})\/(\d{2})$/)
  return m ? `${m[1]}-${m[2]}-${m[3]}` : ''
}
function fromIsoDate(v: string): string {
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  return m ? `${m[1]}/${m[2]}/${m[3]}` : ''
}

// ── add-filter button ────────────────────────────────────────────────────

function AddFilterButton({ disabled, onPick }: { disabled?: boolean; onPick: (op: Op) => void }) {
  const [open, setOpen] = useState(false)
  return (
    <Dropdown open={open} onOpenChange={setOpen}>
      <DropdownTrigger disabled={disabled}>
        <span className={cn(
          'inline-flex items-center gap-1 h-7 px-2 rounded-full text-xs',
          'border border-dashed border-border text-text-muted',
          'hover:bg-surface hover:text-text',
          disabled && 'opacity-50 pointer-events-none',
        )}>
          + Add filter
        </span>
      </DropdownTrigger>
      <DropdownContent className="max-h-[260px] overflow-auto">
        {OPERATORS.map(def => (
          <DropdownItem key={def.op} onClick={() => { onPick(def.op); setOpen(false) }}>
            {def.label}
          </DropdownItem>
        ))}
      </DropdownContent>
    </Dropdown>
  )
}

// ── mode toggle ──────────────────────────────────────────────────────────

function ModeToggle({ mode, setMode, disabled }: {
  mode: 'visual' | 'raw'
  setMode: (m: 'visual' | 'raw') => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      onClick={() => setMode(mode === 'visual' ? 'raw' : 'visual')}
      disabled={disabled}
      className="text-[11px] text-text-muted hover:text-text"
    >
      {mode === 'visual' ? 'Edit raw query →' : '← Visual builder'}
    </button>
  )
}

// Suppress unused-token-type warnings while keeping the union exported in
// case downstream code wants to parse externally.
export type { Token }

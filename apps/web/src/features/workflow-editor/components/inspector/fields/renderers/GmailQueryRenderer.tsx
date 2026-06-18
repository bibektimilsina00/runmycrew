import { useEffect, useRef, useState } from 'react'
import type { RendererProps } from '../types'
import { Toggle } from '@/shared/components'
import { Dropdown, DropdownTrigger, DropdownContent, DropdownItem } from '@/components/ui/dropdown-menu'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
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
      <div className="relative">
        <div className="absolute -top-[20px] right-0 z-10 flex items-center">
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
    <div className="relative">
      <div className="absolute -top-[20px] right-0 z-10 flex items-center">
        <ModeToggle mode={mode} setMode={setMode} disabled={disabled} />
      </div>
      <div className={cn(
        'flex flex-wrap items-center gap-1.5',
        'min-h-[38px] px-3 py-1.5 rounded-[8px]',
        'bg-surface border border-solid border-border-soft transition-colors duration-[120ms]',
        'hover:border-border hover:bg-surface-2 focus-within:border-accent focus-within:bg-surface-2',
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
          className="h-7 py-0 px-2 text-xs flex-1 min-w-[120px] bg-transparent border-0 outline-none focus:ring-0 focus:shadow-none focus-visible:ring-0 focus-visible:bg-transparent focus-visible:border-transparent hover:bg-transparent hover:border-transparent placeholder:text-text-faint text-text"
        />
        <AddFilterButton disabled={disabled} onPick={addChip} />
      </div>
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
      <Button
        type="button"
        variant="ghost"
        onClick={toggleNegate}
        disabled={disabled}
        title={chip.negated ? 'Match messages with this (remove −)' : 'Exclude messages with this (add −)'}
        className={cn(
          'pl-2 pr-0.5 font-mono h-auto p-0 hover:bg-transparent leading-none text-xs',
          chip.negated ? 'text-[var(--danger,#dc2626)]' : 'text-text-muted hover:text-text',
        )}
      >
        {chip.negated ? '−' : ''}
      </Button>
      <span className="text-text-muted">{def.label}:</span>
      {def.kind === 'preset' ? (
        <Dropdown>
          <DropdownTrigger asChild disabled={disabled}>
            <Button
              type="button"
              variant="link"
              className="text-text px-1 h-auto p-0 hover:underline outline-none cursor-pointer text-xs"
            >
              {chip.value || '—'}
            </Button>
          </DropdownTrigger>
          <DropdownContent>
            {def.options!.map(o => (
              <DropdownItem key={o} onClick={() => onChange({ value: o })}>
                {o}
              </DropdownItem>
            ))}
          </DropdownContent>
        </Dropdown>
      ) : editing ? (
        <Input
          ref={inputRef}
          type={def.kind === 'date' ? 'date' : 'text'}
          value={def.kind === 'date' ? toIsoDate(chip.value) : chip.value}
          onChange={(e) => onChange({ value: def.kind === 'date' ? fromIsoDate(e.target.value) : e.target.value })}
          onBlur={commit}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === 'Escape') { e.preventDefault(); commit() } }}
          placeholder={def.placeholder}
          disabled={disabled}
          className="bg-transparent text-text text-xs outline-none border-0 py-0 px-1 min-w-[60px] w-[var(--w,auto)] hover:bg-transparent focus-visible:bg-transparent focus-visible:border-transparent"
          style={{ width: `${Math.max((chip.value?.length ?? 0) + 1, def.placeholder?.length ?? 8)}ch` }}
        />
      ) : (
        <Button
          type="button"
          variant="link"
          onClick={() => setEditing(true)}
          disabled={disabled}
          className="text-text px-1 h-auto p-0 hover:underline text-xs font-normal"
        >
          {valueLabel}
        </Button>
      )}
      <Button
        type="button"
        variant="ghost"
        onClick={onRemove}
        disabled={disabled}
        title="Remove filter"
        className="px-1.5 h-auto p-0 text-text-muted hover:text-text hover:bg-transparent leading-none text-xs"
      >
        ×
      </Button>
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
      <DropdownTrigger asChild disabled={disabled}>
        <Button
          type="button"
          variant="ghost"
          className={cn(
            'inline-flex items-center gap-1 h-7 px-2 rounded-full text-xs hover:bg-surface hover:text-text',
            'border border-dashed border-border text-text-muted',
            disabled && 'opacity-50 pointer-events-none',
          )}
        >
          + Add filter
        </Button>
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
    <label className="inline-flex items-center gap-2 text-[11px] text-text-muted cursor-pointer select-none">
      <span>Raw query</span>
      <Toggle
        checked={mode === 'raw'}
        onChange={(e) => setMode(e.target.checked ? 'raw' : 'visual')}
        disabled={disabled}
        aria-label="Toggle raw query mode"
      />
    </label>
  )
}

// Suppress unused-token-type warnings while keeping the union exported in
// case downstream code wants to parse externally.
export type { Token }

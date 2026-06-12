import { useEffect, useMemo, useRef, useState } from 'react'
import { Plus, X, Search, Lock, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'
import { useToolCatalog, type Tool } from '../../../../hooks/useToolCatalog'

type UsageControl = 'auto' | 'force' | 'none'

interface ToolEntry {
  toolId: string
  usageControl: UsageControl
  kind: 'tool' | 'mcp'
}

function toToolArray(value: unknown): ToolEntry[] {
  if (!value) return []
  const arr =
    typeof value === 'string'
      ? (() => {
          try { return JSON.parse(value) } catch { return [] }
        })()
      : value
  if (!Array.isArray(arr)) return []
  return arr.filter(
    (i): i is ToolEntry =>
      typeof i === 'object' && i !== null && (i as ToolEntry).kind !== 'mcp',
  )
}

const USAGE_LABELS: Record<UsageControl, string> = { auto: 'Auto', force: 'Force', none: 'Off' }
const USAGE_STYLES: Record<UsageControl, string> = {
  auto: 'bg-surface text-text-mute border-border-faint',
  force: 'bg-ok/10 text-ok border-ok/30',
  none: 'bg-err/10 text-err border-err/30',
}

export function ToolSelectorRenderer({ value, onChange }: RendererProps) {
  const tools = toToolArray(value)
  const [pickerOpen, setPickerOpen] = useState(false)
  const catalogQuery = useToolCatalog()
  const catalogData = catalogQuery.data?.tools
  const catalog = useMemo<Tool[]>(() => catalogData ?? [], [catalogData])
  const catalogById = useMemo<Map<string, Tool>>(
    () => new Map(catalog.map(t => [t.id, t])),
    [catalog],
  )

  const remove = (i: number) => onChange(tools.filter((_, j) => j !== i))

  const cycleUsage = (i: number) => {
    const cycle: UsageControl[] = ['auto', 'force', 'none']
    const current = tools[i].usageControl
    const nextUsage = cycle[(cycle.indexOf(current) + 1) % cycle.length]
    onChange(tools.map((t, j) => (j === i ? { ...t, usageControl: nextUsage } : t)))
  }

  const addTool = (toolId: string) => {
    if (tools.some(t => t.toolId === toolId)) {
      setPickerOpen(false)
      return
    }
    onChange([...tools, { toolId, usageControl: 'auto', kind: 'tool' }])
    setPickerOpen(false)
  }

  return (
    <div className="flex flex-col gap-1.5">
      {tools.map((tool, i) => (
        <SelectedToolRow
          key={i}
          entry={tool}
          definition={catalogById.get(tool.toolId)}
          onCycleUsage={() => cycleUsage(i)}
          onRemove={() => remove(i)}
        />
      ))}

      {pickerOpen ? (
        <ToolPicker
          catalog={catalog}
          alreadyAdded={tools.map(t => t.toolId)}
          loading={catalogQuery.isLoading}
          error={catalogQuery.error ? String(catalogQuery.error) : null}
          onPick={addTool}
          onClose={() => setPickerOpen(false)}
        />
      ) : (
        <button
          type="button"
          onClick={() => setPickerOpen(true)}
          className="flex h-7 w-full items-center justify-center gap-1.5 rounded-[5px] border border-dashed border-border-faint text-[11px] text-text-faint hover:border-border-soft hover:text-text-mute transition-colors"
        >
          <Plus size={11} />
          Add tool
        </button>
      )}
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────────
//  Selected tool row
// ──────────────────────────────────────────────────────────────────────────

interface SelectedToolRowProps {
  entry: ToolEntry
  definition: Tool | undefined
  onCycleUsage: () => void
  onRemove: () => void
}

function SelectedToolRow({ entry, definition, onCycleUsage, onRemove }: SelectedToolRowProps) {
  // Tools may be in the saved value but no longer in the catalog (deprecated
  // / removed module). Show them with a warning marker so users know to
  // re-pick before next run.
  const isOrphan = definition === undefined
  return (
    <div
      className={cn(
        'flex items-center gap-1.5 rounded-[5px] border bg-bg px-2.5 py-1.5',
        isOrphan ? 'border-warn/40' : 'border-border-faint',
      )}
    >
      {isOrphan ? (
        <AlertCircle size={11} className="shrink-0 text-warn" />
      ) : definition?.requires_auth ? (
        <Lock size={10} className="shrink-0 text-text-faint" />
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <span className={cn('truncate text-[11.5px]', isOrphan ? 'text-warn' : 'text-text')}>
          {definition?.name ?? entry.toolId}
        </span>
        <span className="truncate font-mono text-[10px] text-text-faint">
          {definition?.category_label ? `${definition.category_label} · ${entry.toolId}` : entry.toolId}
        </span>
      </div>
      <button
        type="button"
        onClick={onCycleUsage}
        className={cn(
          'shrink-0 rounded-[4px] border px-1.5 py-0.5 text-[10px] font-medium transition-colors',
          USAGE_STYLES[entry.usageControl],
        )}
        title="Click to cycle usage control"
      >
        {USAGE_LABELS[entry.usageControl]}
      </button>
      <button
        type="button"
        onClick={onRemove}
        className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-text-faint hover:text-err transition-colors"
      >
        <X size={11} />
      </button>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────────
//  Picker — grouped catalog with search
// ──────────────────────────────────────────────────────────────────────────

interface ToolPickerProps {
  catalog: Tool[]
  alreadyAdded: string[]
  loading: boolean
  error: string | null
  onPick: (toolId: string) => void
  onClose: () => void
}

interface FlatItem {
  kind: 'group' | 'tool'
  groupLabel?: string
  tool?: Tool
}

function ToolPicker({ catalog, alreadyAdded, loading, error, onPick, onClose }: ToolPickerProps) {
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return catalog
    return catalog.filter(
      t =>
        t.id.toLowerCase().includes(q) ||
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q),
    )
  }, [catalog, query])

  // Build flat list with section headers so keyboard navigation stays linear.
  const flatItems = useMemo<FlatItem[]>(() => {
    const items: FlatItem[] = []
    let currentCategory: string | null = null
    for (const tool of filtered) {
      if (tool.category !== currentCategory) {
        currentCategory = tool.category
        items.push({ kind: 'group', groupLabel: tool.category_label })
      }
      items.push({ kind: 'tool', tool })
    }
    return items
  }, [filtered])

  // Flattened tool-only list (used by keyboard handlers — group rows are
  // never selectable).
  const toolItems = useMemo(
    () => flatItems.filter((i): i is FlatItem & { kind: 'tool'; tool: Tool } => i.kind === 'tool'),
    [flatItems],
  )

  // Clamp the highlight to whatever's currently in range — derived, not
  // effect-based, so it stays in lockstep with `toolItems.length` without
  // a render-time setState.
  const clampedIndex = toolItems.length === 0 ? 0 : Math.min(activeIndex, toolItems.length - 1)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (toolItems.length === 0) {
      if (e.key === 'Escape') onClose()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex(i => (i + 1) % toolItems.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex(i => (i - 1 + toolItems.length) % toolItems.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const picked = toolItems[clampedIndex]?.tool
      if (picked) onPick(picked.id)
    } else if (e.key === 'Escape') {
      e.preventDefault()
      onClose()
    }
  }

  // Close when focus leaves the picker (mousedown elsewhere). Tested via
  // relatedTarget so clicks INSIDE the picker (selecting an item) don't
  // close prematurely.
  const handleBlur = (e: React.FocusEvent) => {
    if (wrapperRef.current?.contains(e.relatedTarget as Node | null)) return
    onClose()
  }

  return (
    <div
      ref={wrapperRef}
      onBlur={handleBlur}
      tabIndex={-1}
      className="flex flex-col gap-1 rounded-[5px] border border-border bg-bg p-1.5 shadow-[0_8px_24px_-8px_oklch(0_0_0/0.4)]"
    >
      <div className="flex items-center gap-1.5 rounded-[4px] bg-surface px-2 py-1">
        <Search size={11} className="shrink-0 text-text-faint" />
        <input
          ref={inputRef}
          value={query}
          onChange={e => {
            setQuery(e.target.value)
            setActiveIndex(0)
          }}
          onKeyDown={handleKeyDown}
          placeholder="Search tools…"
          className="flex-1 bg-transparent text-[11.5px] text-text placeholder:text-text-faint outline-none"
        />
        <button
          type="button"
          onClick={onClose}
          className="flex h-4 w-4 shrink-0 items-center justify-center rounded text-text-faint hover:text-text"
          title="Close (Esc)"
        >
          <X size={10} />
        </button>
      </div>

      <div className="max-h-[260px] overflow-y-auto">
        {loading && <PickerStatus message="Loading tools…" />}
        {error && <PickerStatus message={error} variant="error" />}
        {!loading && !error && toolItems.length === 0 && (
          <PickerStatus
            message={query ? `No tools match "${query}"` : 'No tools available'}
          />
        )}
        {!loading &&
          !error &&
          flatItems.map((item, idx) => {
            if (item.kind === 'group') {
              return (
                <div
                  key={`group-${item.groupLabel}-${idx}`}
                  className="px-2 pb-0.5 pt-2 text-[9.5px] font-semibold uppercase tracking-wider text-text-faint"
                >
                  {item.groupLabel}
                </div>
              )
            }
            const tool = item.tool!
            const toolIdx = toolItems.findIndex(t => t.tool!.id === tool.id)
            const active = toolIdx === clampedIndex
            const disabled = alreadyAdded.includes(tool.id)
            return (
              <button
                key={tool.id}
                type="button"
                onMouseDown={e => e.preventDefault()}
                onClick={() => !disabled && onPick(tool.id)}
                disabled={disabled}
                className={cn(
                  'flex w-full items-start gap-2 rounded-[4px] px-2 py-1.5 text-left transition-colors',
                  active && !disabled ? 'bg-surface' : 'hover:bg-surface',
                  disabled && 'opacity-40 cursor-not-allowed',
                )}
              >
                {tool.requires_auth && (
                  <Lock size={10} className="mt-0.5 shrink-0 text-text-faint" />
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2">
                    <span className="truncate text-[12px] text-text">{tool.name}</span>
                    {disabled && (
                      <span className="ml-auto shrink-0 font-mono text-[9.5px] text-text-faint">
                        added
                      </span>
                    )}
                  </div>
                  <p className="line-clamp-2 text-[10.5px] text-text-faint">{tool.description}</p>
                </div>
              </button>
            )
          })}
      </div>
    </div>
  )
}

interface PickerStatusProps {
  message: string
  variant?: 'info' | 'error'
}

function PickerStatus({ message, variant = 'info' }: PickerStatusProps) {
  return (
    <div
      className={cn(
        'px-2 py-3 text-center text-[11px]',
        variant === 'error' ? 'text-err' : 'text-text-faint',
      )}
    >
      {message}
    </div>
  )
}

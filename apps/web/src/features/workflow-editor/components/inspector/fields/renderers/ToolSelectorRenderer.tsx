import { useEffect, useMemo, useRef, useState } from 'react'
import { Plus, X, Search, Lock, AlertCircle, ChevronDown, Eye, EyeOff, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Input, Textarea } from '@/shared/components'
import { CredentialSelector } from '@/shared/components/CredentialSelector'
import type { RendererProps } from '../types'
import { useToolCatalog, useWorkflowTools, type Tool } from '../../../../hooks/useToolCatalog'
import { ExpressionEditor } from '../expression/ExpressionEditor'

type UsageControl = 'auto' | 'force' | 'none'

interface RetryOverride {
  enabled: boolean
  max_retries: number
  initial_delay_ms: number
  max_delay_ms: number
}

interface ToolEntry {
  toolId: string
  usageControl: UsageControl
  kind: 'tool' | 'mcp'
  /**
   * User-preset parameter values for this tool. Each value is merged on top
   * of the LLM-provided args at run time (see agent.py `_resolve_tools`),
   * so the LLM can still override if the param's visibility allows.
   */
  params?: Record<string, unknown>
  /**
   * Credential id pinning this tool to a specific workspace credential.
   * When unset, the backend uses the first credential matching the tool's
   * oauth.credential_type — i.e. the previous behaviour.
   */
  credentialId?: string
  /**
   * Retry-config override. When `enabled` is true, the backend uses these
   * values instead of the tool's built-in `ToolRetryConfig`.
   */
  retry?: RetryOverride
}

const DEFAULT_RETRY: RetryOverride = {
  enabled: true,
  max_retries: 3,
  initial_delay_ms: 1000,
  max_delay_ms: 10000,
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
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)
  const catalogQuery = useToolCatalog()
  const workflowToolsQuery = useWorkflowTools()
  // Merge built-in tools with the workspace's workflows-as-tools. The
  // picker treats them uniformly — they share the same `Tool` shape and
  // grouping logic. Workflows surface under their own `workflow` category.
  const catalog = useMemo<Tool[]>(
    () => [...(catalogQuery.data?.tools ?? []), ...(workflowToolsQuery.data?.tools ?? [])],
    [catalogQuery.data?.tools, workflowToolsQuery.data?.tools],
  )
  const catalogById = useMemo<Map<string, Tool>>(
    () => new Map(catalog.map(t => [t.id, t])),
    [catalog],
  )

  const remove = (i: number) => {
    onChange(tools.filter((_, j) => j !== i))
    if (expandedIndex === i) setExpandedIndex(null)
  }

  const cycleUsage = (i: number) => {
    const cycle: UsageControl[] = ['auto', 'force', 'none']
    const current = tools[i].usageControl
    const nextUsage = cycle[(cycle.indexOf(current) + 1) % cycle.length]
    onChange(tools.map((t, j) => (j === i ? { ...t, usageControl: nextUsage } : t)))
  }

  const updateParams = (i: number, params: Record<string, unknown>) => {
    onChange(tools.map((t, j) => (j === i ? { ...t, params } : t)))
  }

  const updateCredential = (i: number, credentialId: string) => {
    onChange(
      tools.map((t, j) => {
        if (j !== i) return t
        const next = { ...t }
        if (credentialId) next.credentialId = credentialId
        else delete next.credentialId
        return next
      }),
    )
  }

  const updateRetry = (i: number, retry: RetryOverride | undefined) => {
    onChange(
      tools.map((t, j) => {
        if (j !== i) return t
        const next = { ...t }
        if (retry) next.retry = retry
        else delete next.retry
        return next
      }),
    )
  }

  const addTool = (toolId: string) => {
    if (tools.some(t => t.toolId === toolId)) {
      setPickerOpen(false)
      return
    }
    onChange([...tools, { toolId, usageControl: 'auto', kind: 'tool' }])
    setExpandedIndex(tools.length)
    setPickerOpen(false)
  }

  return (
    <div className="flex flex-col gap-1.5">
      {tools.map((tool, i) => (
        <SelectedToolRow
          key={i}
          entry={tool}
          definition={catalogById.get(tool.toolId)}
          expanded={expandedIndex === i}
          onToggleExpand={() => setExpandedIndex(expandedIndex === i ? null : i)}
          onCycleUsage={() => cycleUsage(i)}
          onRemove={() => remove(i)}
          onChangeParams={params => updateParams(i, params)}
          onChangeCredential={credId => updateCredential(i, credId)}
          onChangeRetry={retry => updateRetry(i, retry)}
        />
      ))}

      {pickerOpen ? (
        <ToolPicker
          catalog={catalog}
          alreadyAdded={tools.map(t => t.toolId)}
          loading={catalogQuery.isLoading || workflowToolsQuery.isLoading}
          error={
            catalogQuery.error
              ? String(catalogQuery.error)
              : workflowToolsQuery.error
                ? String(workflowToolsQuery.error)
                : null
          }
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
  expanded: boolean
  onToggleExpand: () => void
  onCycleUsage: () => void
  onRemove: () => void
  onChangeParams: (params: Record<string, unknown>) => void
  onChangeCredential: (credentialId: string) => void
  onChangeRetry: (retry: RetryOverride | undefined) => void
}

function SelectedToolRow({
  entry,
  definition,
  expanded,
  onToggleExpand,
  onCycleUsage,
  onRemove,
  onChangeParams,
  onChangeCredential,
  onChangeRetry,
}: SelectedToolRowProps) {
  const isOrphan = definition === undefined

  // Tools become expandable when there's something to configure: at least
  // one user-visible param, OR they need a credential, OR they expose a
  // retry config (every registered tool does, but we still need the gate
  // for orphaned saved entries with no definition).
  const userVisibleParams = useMemo(
    () =>
      definition
        ? Object.entries(definition.params).filter(
            ([, p]) => p.visibility === 'user-only' || p.visibility === 'user-or-llm',
          )
        : [],
    [definition],
  )
  const hasConfigurable =
    userVisibleParams.length > 0 || Boolean(definition?.requires_auth) || Boolean(definition)

  return (
    <div
      className={cn(
        'flex flex-col rounded-[5px] border bg-bg',
        isOrphan ? 'border-warn/40' : 'border-border-faint',
      )}
    >
      <div className="flex items-center gap-1.5 px-2.5 py-1.5">
        {hasConfigurable ? (
          <button
            type="button"
            onClick={onToggleExpand}
            className="flex h-4 w-4 shrink-0 items-center justify-center rounded text-text-faint hover:text-text-mute"
            title={expanded ? 'Collapse' : 'Configure'}
          >
            <ChevronDown
              size={11}
              className={cn('transition-transform', expanded && 'rotate-180')}
            />
          </button>
        ) : (
          <div className="h-4 w-4 shrink-0" />
        )}

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
            {definition?.category_label
              ? `${definition.category_label} · ${entry.toolId}`
              : entry.toolId}
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

      {expanded && hasConfigurable && definition && (
        <ToolConfigPanel
          definition={definition}
          params={entry.params ?? {}}
          onChangeParams={onChangeParams}
          credentialId={entry.credentialId ?? ''}
          onChangeCredential={onChangeCredential}
          retry={entry.retry}
          onChangeRetry={onChangeRetry}
        />
      )}
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────────
//  Tool config panel (expanded body)
// ──────────────────────────────────────────────────────────────────────────

interface ToolConfigPanelProps {
  definition: Tool
  params: Record<string, unknown>
  onChangeParams: (params: Record<string, unknown>) => void
  credentialId: string
  onChangeCredential: (credentialId: string) => void
  retry: RetryOverride | undefined
  onChangeRetry: (retry: RetryOverride | undefined) => void
}

function ToolConfigPanel({
  definition,
  params,
  onChangeParams,
  credentialId,
  onChangeCredential,
  retry,
  onChangeRetry,
}: ToolConfigPanelProps) {
  const entries = useMemo(
    () =>
      Object.entries(definition.params).filter(
        ([, p]) => p.visibility === 'user-only' || p.visibility === 'user-or-llm',
      ),
    [definition.params],
  )

  const setParam = (name: string, value: unknown) => {
    if (value === '' || value === undefined) {
      // Unset rather than store empty so the merge with LLM args still
      // gives the model a chance to fill in.
      const next = { ...params }
      delete next[name]
      onChangeParams(next)
    } else {
      onChangeParams({ ...params, [name]: value })
    }
  }

  return (
    <div className="flex flex-col gap-3 border-t border-border-faint px-2.5 py-2">
      {definition.requires_auth && definition.oauth && (
        <ConfigSection title="Credential" hint="Pinning a credential overrides the workspace default.">
          <CredentialSelector
            credType={definition.oauth.credential_type}
            value={credentialId}
            onChange={onChangeCredential}
          />
        </ConfigSection>
      )}

      {entries.length > 0 && (
        <ConfigSection title="Parameters">
          <div className="flex flex-col gap-2">
            {entries.map(([name, def]) => (
              <ParamField
                key={name}
                name={name}
                paramType={def.type}
                required={def.required}
                visibility={def.visibility}
                description={def.description}
                value={params[name]}
                onChange={v => setParam(name, v)}
              />
            ))}
          </div>
        </ConfigSection>
      )}

      <ConfigSection title="Retry">
        <RetryConfig value={retry} onChange={onChangeRetry} />
      </ConfigSection>
    </div>
  )
}

function ConfigSection({
  title,
  hint,
  children,
}: {
  title: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[9.5px] uppercase tracking-wider text-text-faint">
          {title}
        </span>
        {hint && <span className="text-[9.5px] text-text-faint">{hint}</span>}
      </div>
      {children}
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────────
//  ParamField — per-type editor
// ──────────────────────────────────────────────────────────────────────────

interface ParamFieldProps {
  name: string
  paramType: string
  required: boolean
  visibility: string
  description: string
  value: unknown
  onChange: (value: unknown) => void
}

function ParamField({
  name,
  paramType,
  required,
  visibility,
  description,
  value,
  onChange,
}: ParamFieldProps) {
  // Visibility badge — clarifies the LLM/user contract per param.
  const visibilityBadge =
    visibility === 'user-only' ? (
      <span
        className="inline-flex items-center gap-1 rounded-[3px] bg-surface px-1 py-0.5 font-mono text-[9px] text-text-faint"
        title="User-only: hidden from the LLM"
      >
        <EyeOff size={8} />
        user only
      </span>
    ) : (
      <span
        className="inline-flex items-center gap-1 rounded-[3px] bg-surface px-1 py-0.5 font-mono text-[9px] text-text-faint"
        title="User or LLM: your preset overrides what the LLM picks"
      >
        <Eye size={8} />
        user or LLM
      </span>
    )

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between gap-2">
        <label className="font-mono text-[10.5px] uppercase tracking-wide text-text-mute">
          {name}
          {required && <span className="ml-0.5 text-err">*</span>}
        </label>
        {visibilityBadge}
      </div>
      <ParamInput paramType={paramType} value={value} onChange={onChange} placeholder={description} />
      {description && (
        <p className="text-[10.5px] leading-relaxed text-text-faint">{description}</p>
      )}
    </div>
  )
}

interface ParamInputProps {
  paramType: string
  value: unknown
  onChange: (value: unknown) => void
  placeholder?: string
}

function ParamInput({ paramType, value, onChange, placeholder }: ParamInputProps) {
  if (paramType === 'boolean') {
    return <BooleanParam value={value} onChange={onChange} />
  }
  if (paramType === 'number') {
    return <NumberParam value={value} onChange={onChange} placeholder={placeholder} />
  }
  if (paramType === 'json') {
    return <JsonParam value={value} onChange={onChange} placeholder={placeholder} />
  }
  // string + fallback
  return <StringParam value={value} onChange={onChange} placeholder={placeholder} />
}

// ── String param with inline expression-mode swap ──────────────────────────

function StringParam({
  value,
  onChange,
  placeholder,
}: {
  value: unknown
  onChange: (v: unknown) => void
  placeholder?: string
}) {
  const str = value === undefined || value === null ? '' : String(value)
  const isExpression = str.startsWith('=')

  const [autoFocusOnEnter, setAutoFocusOnEnter] = useState(false)
  const [autoFocusOnExit, setAutoFocusOnExit] = useState(false)
  const plainRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!autoFocusOnExit) return
    const el = plainRef.current
    if (!el) return
    el.focus()
    el.setSelectionRange(el.value.length, el.value.length)
    setAutoFocusOnExit(false)
  }, [autoFocusOnExit])

  const toggleMode = () => {
    if (isExpression) {
      setAutoFocusOnExit(true)
      onChange(str.slice(1))
    } else {
      setAutoFocusOnEnter(true)
      onChange(`=${str}`)
    }
  }

  const handlePlain = (next: string) => {
    if (!str.startsWith('=') && (next.startsWith('=') || next.startsWith('$'))) {
      setAutoFocusOnEnter(true)
    }
    if (next.startsWith('$') && !str.startsWith('=')) {
      onChange(`=${next}`)
      return
    }
    onChange(next)
  }

  const handleExpression = (next: string) => {
    if (!next.startsWith('=') && str.startsWith('=')) {
      setAutoFocusOnExit(true)
    }
    onChange(next)
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={toggleMode}
        title={isExpression ? 'Switch to plain text' : 'Switch to expression (JSONata)'}
        aria-pressed={isExpression}
        className={cn(
          'absolute -top-[18px] right-0 flex h-[14px] items-center rounded-[3px] px-1',
          'font-mono text-[9px] font-semibold uppercase tracking-wide leading-none',
          'transition-colors',
          isExpression
            ? 'bg-accent/15 text-accent hover:bg-accent/25'
            : 'text-text-faint hover:bg-accent/15 hover:text-accent',
        )}
      >
        fx
      </button>
      {isExpression ? (
        <ExpressionEditor
          value={str}
          onChange={handleExpression}
          placeholder={placeholder}
          autoFocus={autoFocusOnEnter}
          onAutoFocusDone={() => setAutoFocusOnEnter(false)}
        />
      ) : (
        <Input
          ref={plainRef}
          value={str}
          onChange={e => handlePlain(e.target.value)}
          placeholder={placeholder}
          className="h-7 rounded-[4px] text-[11px]"
        />
      )}
    </div>
  )
}

// ── Number param ─────────────────────────────────────────────────────────

function NumberParam({
  value,
  onChange,
  placeholder,
}: {
  value: unknown
  onChange: (v: unknown) => void
  placeholder?: string
}) {
  const str = value === undefined || value === null ? '' : String(value)
  return (
    <Input
      type="number"
      value={str}
      onChange={e => onChange(e.target.value === '' ? '' : Number(e.target.value))}
      placeholder={placeholder}
      className="h-7 rounded-[4px] text-[11px]"
    />
  )
}

// ── Boolean param ────────────────────────────────────────────────────────

function BooleanParam({
  value,
  onChange,
}: {
  value: unknown
  onChange: (v: unknown) => void
}) {
  const checked = Boolean(value)
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      role="switch"
      aria-checked={checked}
      className={cn(
        'flex h-7 w-fit items-center gap-2 rounded-[4px] border px-2 text-[11px] transition-colors',
        checked
          ? 'border-accent/40 bg-accent/10 text-accent'
          : 'border-border-faint bg-bg text-text-mute hover:border-border-soft',
      )}
    >
      <span
        className={cn(
          'inline-block h-2.5 w-2.5 rounded-full',
          checked ? 'bg-accent' : 'bg-border-soft',
        )}
      />
      {checked ? 'true' : 'false'}
    </button>
  )
}

// ── JSON param ───────────────────────────────────────────────────────────

function JsonParam({
  value,
  onChange,
  placeholder,
}: {
  value: unknown
  onChange: (v: unknown) => void
  placeholder?: string
}) {
  const initialRaw =
    value === undefined || value === null
      ? ''
      : typeof value === 'string'
        ? value
        : JSON.stringify(value, null, 2)
  const [raw, setRaw] = useState(initialRaw)
  const [invalid, setInvalid] = useState(false)

  const commit = (next: string) => {
    setRaw(next)
    if (next.trim() === '') {
      setInvalid(false)
      onChange(undefined)
      return
    }
    try {
      onChange(JSON.parse(next))
      setInvalid(false)
    } catch {
      setInvalid(true)
    }
  }

  return (
    <div className="flex flex-col gap-1">
      <Textarea
        value={raw}
        onChange={e => commit(e.target.value)}
        rows={3}
        spellCheck={false}
        placeholder={placeholder ?? '{}'}
        className={cn(
          'rounded-[4px] font-mono text-[10.5px] leading-relaxed',
          invalid && 'border-err focus-visible:ring-err/30',
        )}
      />
      {invalid && <p className="text-[10px] text-err">Invalid JSON</p>}
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────────
//  Retry config override
// ──────────────────────────────────────────────────────────────────────────

interface RetryConfigProps {
  value: RetryOverride | undefined
  onChange: (next: RetryOverride | undefined) => void
}

function RetryConfig({ value, onChange }: RetryConfigProps) {
  const enabled = Boolean(value?.enabled)
  const cfg = value ?? DEFAULT_RETRY

  const set = (patch: Partial<RetryOverride>) => onChange({ ...cfg, ...patch })

  return (
    <div className="flex flex-col gap-1.5">
      <button
        type="button"
        onClick={() => onChange(enabled ? undefined : { ...DEFAULT_RETRY, enabled: true })}
        role="switch"
        aria-checked={enabled}
        className={cn(
          'flex h-7 w-fit items-center gap-2 rounded-[4px] border px-2 text-[11px] transition-colors',
          enabled
            ? 'border-accent/40 bg-accent/10 text-accent'
            : 'border-border-faint bg-bg text-text-mute hover:border-border-soft',
        )}
      >
        <RefreshCw size={11} />
        {enabled ? 'Custom retry on' : 'Use tool defaults'}
      </button>
      {enabled && (
        <div className="grid grid-cols-3 gap-1.5">
          <RetryNumberField
            label="Max retries"
            value={cfg.max_retries}
            min={0}
            onChange={v => set({ max_retries: v })}
          />
          <RetryNumberField
            label="Initial (ms)"
            value={cfg.initial_delay_ms}
            min={0}
            onChange={v => set({ initial_delay_ms: v })}
          />
          <RetryNumberField
            label="Max (ms)"
            value={cfg.max_delay_ms}
            min={0}
            onChange={v => set({ max_delay_ms: v })}
          />
        </div>
      )}
    </div>
  )
}

function RetryNumberField({
  label,
  value,
  min,
  onChange,
}: {
  label: string
  value: number
  min?: number
  onChange: (v: number) => void
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="font-mono text-[9.5px] uppercase tracking-wide text-text-faint">{label}</span>
      <Input
        type="number"
        min={min !== undefined ? String(min) : undefined}
        value={String(value)}
        onChange={e => {
          const n = Number(e.target.value)
          if (Number.isFinite(n)) onChange(n)
        }}
        className="h-7 rounded-[4px] text-[11px]"
      />
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

  const toolItems = useMemo(
    () => flatItems.filter((i): i is FlatItem & { kind: 'tool'; tool: Tool } => i.kind === 'tool'),
    [flatItems],
  )

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

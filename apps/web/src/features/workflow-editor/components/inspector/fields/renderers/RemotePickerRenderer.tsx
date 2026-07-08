import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Check, ChevronDown, ListPlus, Loader2, Pencil, RefreshCw, Search } from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import { ExpressionEditor } from '../expression/ExpressionEditor'
import type { RendererProps } from '../types'

/**
 * Generic remote-picker renderer.
 *
 * Any field whose manifest carries a `remote` descriptor routes here
 * (see `PropertyField.tsx`). Behaviour:
 *
 *   - Two modes: `list` (credential-scoped searchable dropdown, fetched
 *     from the backend) and `manual` (falls through to `ExpressionEditor`
 *     so `{{ expression }}` and paste-an-id still work).
 *   - The mode toggle at the top only shows when `remote.allow_manual`
 *     is true (default).
 *   - `remote.params` values may reference sibling fields via
 *     `${field_name}` — resolved from the current node's `properties`
 *     bag at fetch time.
 *   - `remote.depends_on` lists sibling fields whose value change should
 *     invalidate the cached options. React Query keys off the resolved
 *     params so this happens automatically.
 *   - States: no-credential, missing-dep, loading, empty, error, list.
 *
 * The list picker keeps the field value as a bare id string — same
 * shape the backend `LookupItem.id` returns and the same shape
 * workflow graphs stored today. Existing serialised graphs keep
 * working.
 */

interface LookupItem {
  id: string
  label: string
  sublabel?: string | null
  icon_slug?: string | null
}

interface LookupResponse {
  items: LookupItem[]
  cursor: string | null
  has_more: boolean
}

const DEBOUNCE_MS = 300

export function RemotePickerRenderer({ prop, value, onChange, properties, disabled }: RendererProps) {
  const remote = prop.remote
  const credentialId = typeof properties?.credential === 'string' ? (properties.credential as string) : ''
  const [mode, setMode] = useState<'list' | 'manual'>('list')
  const currentValue = typeof value === 'string' ? value : value == null ? '' : String(value)

  // Resolve `${field}` templates in params from the sibling properties
  // bag. Missing values collapse to empty strings — handlers decide
  // whether that means "return nothing" or "list everything".
  const resolvedParams = useMemo(() => {
    if (!remote) return {}
    const out: Record<string, string> = {}
    for (const [k, tmpl] of Object.entries(remote.params ?? {})) {
      out[k] = tmpl.replace(/\$\{([a-zA-Z0-9_]+)\}/g, (_m, name) => {
        const raw = properties?.[name]
        return typeof raw === 'string' ? raw : raw == null ? '' : String(raw)
      })
    }
    return out
  }, [remote, properties])

  const missingDep = useMemo(() => {
    if (!remote?.depends_on?.length) return null
    for (const dep of remote.depends_on) {
      const v = resolvedParams[dep] ?? (properties?.[dep] as string | undefined) ?? ''
      if (!v) return dep
    }
    return null
  }, [remote, resolvedParams, properties])

  if (!remote) return null

  const enabled = !!credentialId && !missingDep && mode === 'list' && !disabled

  return (
    <div className="flex flex-col gap-1.5">
      {remote.allow_manual && (
        <ModeToggle mode={mode} onChange={setMode} />
      )}
      {mode === 'manual' ? (
        <ExpressionEditor
          value={currentValue}
          onChange={onChange}
          placeholder={prop.placeholder}
          disabled={disabled}
        />
      ) : (
        <RemoteList
          credentialId={credentialId}
          provider={remote.provider}
          resource={remote.resource}
          params={resolvedParams}
          missingDep={missingDep}
          enabled={enabled}
          value={currentValue}
          onChange={onChange}
          onFlipToManual={() => setMode('manual')}
          allowManual={remote.allow_manual}
        />
      )}
    </div>
  )
}

function ModeToggle({ mode, onChange }: { mode: 'list' | 'manual'; onChange: (m: 'list' | 'manual') => void }) {
  return (
    <div className="inline-flex items-center rounded-[7px] border border-[var(--border-faint)] bg-[var(--surface)] p-[2px]">
      <ModeButton active={mode === 'list'} onClick={() => onChange('list')} icon={<ListPlus className="h-3 w-3" />} label="From list" />
      <ModeButton active={mode === 'manual'} onClick={() => onChange('manual')} icon={<Pencil className="h-3 w-3" />} label="Manual" />
    </div>
  )
}

function ModeButton({ active, onClick, icon, label }: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-[5px] px-2 py-[3px] text-[11px] font-medium transition-colors',
        active
          ? 'bg-[var(--bg-2)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]'
          : 'text-[var(--text-mute)] hover:text-[var(--text)]',
      )}
    >
      {icon}
      {label}
    </button>
  )
}

interface RemoteListProps {
  credentialId: string
  provider: string
  resource: string
  params: Record<string, string>
  missingDep: string | null
  enabled: boolean
  value: string
  onChange: (v: unknown) => void
  onFlipToManual: () => void
  allowManual: boolean
}

function RemoteList({
  credentialId,
  provider,
  resource,
  params,
  missingDep,
  enabled,
  value,
  onChange,
  onFlipToManual,
  allowManual,
}: RemoteListProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [debounced, setDebounced] = useState('')
  const rootRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const h = window.setTimeout(() => setDebounced(query.trim()), DEBOUNCE_MS)
    return () => window.clearTimeout(h)
  }, [query])

  // Close on outside click.
  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    window.addEventListener('mousedown', onDown)
    return () => window.removeEventListener('mousedown', onDown)
  }, [open])

  useEffect(() => {
    if (open) searchRef.current?.focus()
  }, [open])

  // React Query key intentionally serialises `params` so `depends_on`
  // changes invalidate the cache with zero manual bookkeeping.
  const paramsKey = useMemo(() => JSON.stringify(params), [params])
  const q = useQuery<LookupResponse>({
    queryKey: ['remote-lookup', credentialId, provider, resource, paramsKey, debounced],
    queryFn: async ({ signal }) => {
      const query: Record<string, string> = { ...params }
      if (debounced) query.q = debounced
      const res = await apiClient.get<LookupResponse>(
        `/credentials/${credentialId}/lookup/${provider}/${resource}`,
        { params: query, signal },
      )
      return res.data
    },
    enabled: enabled && open,
    staleTime: 30_000,
  })

  const selected = q.data?.items.find(it => it.id === value)
  const triggerLabel = selected?.label || value

  const disabledReason = !credentialId
    ? 'Select a credential first'
    : missingDep
      ? `Set ${missingDep.replace(/_/g, ' ')} first`
      : null

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => !disabledReason && setOpen(o => !o)}
        disabled={!!disabledReason}
        className={cn(
          'flex h-9 w-full items-center gap-2 rounded-[8px] border border-border-soft bg-surface px-3 text-left text-sm',
          'transition-[background-color,border-color] [transition-duration:120ms]',
          'hover:border-border hover:bg-surface-2',
          'focus:outline-none focus:border-accent focus:bg-surface-2',
          open && 'border-accent bg-surface-2',
          disabledReason && 'cursor-not-allowed opacity-60',
        )}
      >
        <span className={cn('truncate flex-1', triggerLabel ? 'text-text font-mono text-[13px]' : 'text-text-faint')}>
          {disabledReason ?? triggerLabel ?? `Select ${resource}…`}
        </span>
        <ChevronDown className="ml-auto h-3.5 w-3.5 shrink-0 text-text-faint" />
      </button>

      {open && !disabledReason && (
        <div className="absolute z-40 mt-1 w-full overflow-hidden rounded-[10px] border border-border shadow-[0_18px_40px_-10px_oklch(0_0_0/0.6)]" style={{ background: 'var(--bg-2)' }}>
          <div className="flex items-center gap-2 border-b border-[var(--border-faint)] px-2.5 py-1.5">
            <Search className="h-3.5 w-3.5 text-[var(--text-faint)]" />
            <input
              ref={searchRef}
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder={`Search ${resource}…`}
              className="flex-1 bg-transparent text-[12.5px] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)]"
            />
            <button
              type="button"
              onClick={() => q.refetch()}
              title="Refresh"
              className="rounded p-1 text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)]"
            >
              <RefreshCw className={cn('h-3.5 w-3.5', q.isFetching && 'animate-spin')} />
            </button>
          </div>

          <div className="max-h-[280px] overflow-y-auto">
            {q.isLoading ? (
              <RowState icon={<Loader2 className="h-3.5 w-3.5 animate-spin" />} label="Loading…" />
            ) : q.isError ? (
              <div className="flex flex-col gap-2 px-3 py-3">
                <div className="flex items-center gap-2 text-[12px] text-[var(--err)]">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  <span>Couldn't load {resource}.</span>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => q.refetch()}
                    className="rounded-[6px] border border-[var(--border-faint)] px-2 py-1 text-[11px] text-[var(--text)] hover:bg-[var(--surface)]"
                  >
                    Try again
                  </button>
                  {allowManual && (
                    <button
                      type="button"
                      onClick={onFlipToManual}
                      className="rounded-[6px] border border-[var(--border-faint)] px-2 py-1 text-[11px] text-[var(--text-mute)] hover:bg-[var(--surface)]"
                    >
                      Enter manually
                    </button>
                  )}
                </div>
              </div>
            ) : q.data?.items.length ? (
              <>
                <div className="px-2 py-1 text-[9.5px] font-semibold uppercase tracking-widest text-[var(--text-dim)]">
                  {resource} · {q.data.items.length}{q.data.has_more ? '+' : ''}
                </div>
                {q.data.items.map(item => {
                  const active = item.id === value
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        onChange(item.id)
                        setOpen(false)
                      }}
                      className={cn(
                        'flex w-full items-center gap-2.5 px-2.5 py-1.5 text-left transition-colors',
                        active
                          ? 'bg-[color-mix(in_oklab,var(--accent)_16%,transparent)]'
                          : 'hover:bg-[var(--surface)]',
                      )}
                    >
                      <span className="flex min-w-0 flex-1 flex-col">
                        <span className={cn('truncate text-[12.5px]', active ? 'font-semibold text-[var(--text)]' : 'text-[var(--text)]')}>
                          {item.label}
                        </span>
                        {item.sublabel && (
                          <span className="truncate text-[10.5px] text-[var(--text-faint)]">{item.sublabel}</span>
                        )}
                      </span>
                      {active && <Check className="h-3.5 w-3.5 text-[var(--accent)]" />}
                    </button>
                  )
                })}
              </>
            ) : (
              <RowState
                icon={<Search className="h-3.5 w-3.5 text-[var(--text-dim)]" />}
                label={query ? `No ${resource} match "${query}"` : `No ${resource} found`}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function RowState({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-6 text-[12px] text-[var(--text-faint)]">
      {icon}
      <span>{label}</span>
    </div>
  )
}

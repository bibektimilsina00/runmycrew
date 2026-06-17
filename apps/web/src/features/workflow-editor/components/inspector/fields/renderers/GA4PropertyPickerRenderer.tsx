import { useEffect, useMemo, useRef, useState } from 'react'
import {
  BarChart3,
  Check,
  ChevronDown,
  Loader2,
  Search,
  X,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import { ApiErrorMessage } from './ApiErrorMessage'
import type { RendererProps } from '../types'

/**
 * Google Analytics 4 property picker — searchable dropdown grouped
 * by GA4 account. Backed by `/credentials/{cid}/ga4/properties`
 * which fetches every visible account in parallel and flattens the
 * result so the picker stays one network call.
 *
 * Stored value: `{ id, name, displayName, account, accountDisplayName }`.
 * Pydantic on the runtime side accepts the dict shape OR a bare
 * numeric id OR the full `properties/{id}` path.
 */

interface PickerValue {
  id: string
  name: string
  displayName: string
  account: string
  accountDisplayName: string
}

interface PropertyEntry {
  id: string
  name: string
  displayName: string
  account: string
  accountDisplayName: string
  currencyCode?: string
  timeZone?: string
}

interface PropertiesResponse {
  properties: PropertyEntry[]
}

function parseValue(v: unknown): PickerValue | null {
  if (typeof v === 'string') {
    if (!v) return null
    const id = v.startsWith('properties/') ? v.slice('properties/'.length) : v
    return {
      id,
      name: `properties/${id}`,
      displayName: id,
      account: '',
      accountDisplayName: '',
    }
  }
  if (v && typeof v === 'object' && 'id' in v) {
    const obj = v as Partial<PickerValue> & { id?: string }
    if (typeof obj.id === 'string' && obj.id) {
      return {
        id: obj.id,
        name: obj.name || `properties/${obj.id}`,
        displayName: obj.displayName || obj.id,
        account: obj.account || '',
        accountDisplayName: obj.accountDisplayName || '',
      }
    }
  }
  return null
}

export function GA4PropertyPickerRenderer({
  value,
  onChange,
  disabled,
  properties,
}: RendererProps) {
  const selected = parseValue(value)
  const credentialId =
    typeof properties?.credential === 'string' ? properties.credential : ''

  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [items, setItems] = useState<PropertyEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wrapRef = useRef<HTMLDivElement | null>(null)
  const searchRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!open || !credentialId) return
    let alive = true
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)
    apiClient
      .get<PropertiesResponse>(`/credentials/${credentialId}/ga4/properties`)
      .then(({ data }) => {
        if (!alive) return
        setItems(data.properties || [])
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load GA4 properties'
        setError(String(msg))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [open, credentialId])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setItems(null)
    setQuery('')
  }, [credentialId])

  useEffect(() => {
    if (!open) return
    const onMouse = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onMouse)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onMouse)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  useEffect(() => {
    if (open) searchRef.current?.focus()
  }, [open])

  const pickAndClose = (entry: PropertyEntry) => {
    onChange({
      id: entry.id,
      name: entry.name,
      displayName: entry.displayName || entry.id,
      account: entry.account,
      accountDisplayName: entry.accountDisplayName,
    })
    setOpen(false)
    setQuery('')
  }

  // Filter + group by account so the list reads as "Account → properties"
  // even with hundreds of properties across many accounts.
  const grouped = useMemo(() => {
    if (!items) return null
    const q = query.trim().toLowerCase()
    const matches = q
      ? items.filter(
          (p) =>
            p.displayName.toLowerCase().includes(q) ||
            p.id.toLowerCase().includes(q) ||
            p.accountDisplayName.toLowerCase().includes(q),
        )
      : items
    const groups = new Map<string, { label: string; rows: PropertyEntry[] }>()
    for (const p of matches) {
      const key = p.account || '(unknown account)'
      const label = p.accountDisplayName || key
      const entry = groups.get(key) ?? { label, rows: [] }
      entry.rows.push(p)
      groups.set(key, entry)
    }
    return Array.from(groups.values())
  }, [items, query])

  const triggerDisabled = disabled || !credentialId

  return (
    <div ref={wrapRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={triggerDisabled}
        title={!credentialId ? 'Pick a Google account on this node first.' : undefined}
        className={cn(
          'flex w-full items-center gap-2 rounded-[6px] border bg-surface px-2.5 py-1.5',
          'text-left text-[12px] transition-colors',
          open ? 'border-accent' : 'border-border-faint hover:border-text-faint',
          triggerDisabled && 'cursor-not-allowed opacity-50',
        )}
      >
        <BarChart3 className="h-3.5 w-3.5 shrink-0 text-[#f4b400]" />
        <span
          className={cn(
            'min-w-0 flex-1 truncate',
            selected ? 'font-medium text-text' : 'text-text-faint',
          )}
        >
          {selected
            ? selected.displayName
            : credentialId
              ? 'Pick a GA4 property…'
              : 'Pick a Google account first'}
        </span>
        {selected && !triggerDisabled && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onChange('')
            }}
            className="rounded-[4px] p-0.5 text-text-faint hover:bg-surface-2 hover:text-text"
            title="Clear"
          >
            <X className="h-3 w-3" />
          </button>
        )}
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 shrink-0 text-text-faint transition-transform',
            open && 'rotate-180',
          )}
        />
      </button>

      {open && credentialId && (
        <div
          className={cn(
            'absolute z-30 mt-1 w-full overflow-hidden rounded-[8px] border border-border-faint',
            'bg-bg2 shadow-lg',
          )}
        >
          <div className="border-b border-border-faint p-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-text-faint" />
              <input
                ref={searchRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Filter properties or accounts…"
                className={cn(
                  'h-7 w-full rounded-[5px] bg-surface pl-7 pr-2 text-[12px] text-text',
                  'outline-none placeholder:text-text-faint',
                  'focus:ring-1 focus:ring-accent',
                )}
              />
            </div>
          </div>

          <div className="max-h-[320px] overflow-y-auto">
            {loading && !items && (
              <div className="flex items-center justify-center gap-2 py-6 text-[12px] text-text-muted">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Loading…
              </div>
            )}
            {error && !loading && <ApiErrorMessage error={error} compact />}
            {!loading && !error && grouped && grouped.length === 0 && (
              <div className="px-3 py-6 text-center text-[11.5px] text-text-muted">
                {query
                  ? `No GA4 properties matching "${query}".`
                  : 'No GA4 properties visible to this Google account.'}
              </div>
            )}
            {!error && grouped && grouped.length > 0 && (
              <ul>
                {grouped.map((group) => (
                  <li key={group.label}>
                    <div className="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wide text-text-faint">
                      {group.label}
                    </div>
                    <ul>
                      {group.rows.map((p) => {
                        const isSelected = selected?.id === p.id
                        const label = p.displayName || p.id
                        return (
                          <li key={p.id}>
                            <button
                              type="button"
                              onClick={() => pickAndClose(p)}
                              className={cn(
                                'flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px]',
                                'transition-colors hover:bg-surface-2',
                                isSelected && 'bg-surface-2',
                              )}
                            >
                              <BarChart3 className="h-3.5 w-3.5 shrink-0 text-[#f4b400]" />
                              <div className="min-w-0 flex-1">
                                <div className="truncate text-text" title={label}>
                                  {label}
                                </div>
                                <div className="truncate text-[10.5px] text-text-faint">
                                  {p.id}
                                  {p.timeZone ? ` · ${p.timeZone}` : ''}
                                  {p.currencyCode ? ` · ${p.currencyCode}` : ''}
                                </div>
                              </div>
                              {isSelected && (
                                <Check className="h-3.5 w-3.5 shrink-0 text-accent" />
                              )}
                            </button>
                          </li>
                        )
                      })}
                    </ul>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

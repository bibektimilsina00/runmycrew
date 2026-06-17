import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Check,
  ChevronDown,
  Globe,
  Loader2,
  Search,
  Server,
  X,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import { ApiErrorMessage } from './ApiErrorMessage'
import type { RendererProps } from '../types'

/**
 * Google Search Console site picker — dropdown of every verified
 * property the connected account can access. Domain properties get
 * a `Server` icon, URL-prefix properties get a `Globe`.
 *
 * Backend: `GET /credentials/{cid}/gsc/sites?q=...`.
 *
 * Stored value: `{ siteUrl, permissionLevel, isDomainProperty }`.
 * The Pydantic side accepts the dict shape OR a bare URL string —
 * runtime always sends the literal URL to the API (URL-encoded as a
 * path segment, no canonicalisation beyond trailing-slash for plain
 * hostnames).
 */

interface PickerValue {
  siteUrl: string
  permissionLevel: string
  isDomainProperty: boolean
}

interface SiteEntry {
  siteUrl: string
  permissionLevel: string
  isDomainProperty: boolean
}

interface SitesResponse {
  sites: SiteEntry[]
}

function parseValue(v: unknown): PickerValue | null {
  if (typeof v === 'string') {
    if (!v) return null
    return {
      siteUrl: v,
      permissionLevel: '',
      isDomainProperty: v.startsWith('sc-domain:'),
    }
  }
  if (v && typeof v === 'object' && 'siteUrl' in v) {
    const obj = v as Partial<PickerValue> & { siteUrl?: string }
    if (typeof obj.siteUrl === 'string' && obj.siteUrl) {
      return {
        siteUrl: obj.siteUrl,
        permissionLevel: obj.permissionLevel || '',
        isDomainProperty:
          typeof obj.isDomainProperty === 'boolean'
            ? obj.isDomainProperty
            : obj.siteUrl.startsWith('sc-domain:'),
      }
    }
  }
  return null
}

function prettySiteLabel(siteUrl: string): string {
  if (siteUrl.startsWith('sc-domain:')) {
    return siteUrl.slice('sc-domain:'.length)
  }
  // Strip trailing slash for display only; runtime keeps the slash.
  return siteUrl.replace(/\/$/, '')
}

function SiteIcon({
  isDomain,
  className,
}: {
  isDomain: boolean
  className?: string
}) {
  if (isDomain) return <Server className={className} />
  return <Globe className={className} />
}

export function GSCSitePickerRenderer({
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
  const [items, setItems] = useState<SiteEntry[] | null>(null)
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
      .get<SitesResponse>(`/credentials/${credentialId}/gsc/sites`)
      .then(({ data }) => {
        if (!alive) return
        setItems(data.sites || [])
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load Search Console sites'
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

  const pickAndClose = (entry: SiteEntry) => {
    onChange({
      siteUrl: entry.siteUrl,
      permissionLevel: entry.permissionLevel,
      isDomainProperty: entry.isDomainProperty,
    })
    setOpen(false)
    setQuery('')
  }

  const filtered = useMemo(() => {
    if (!items) return null
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter((s) => s.siteUrl.toLowerCase().includes(q))
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
        <SiteIcon
          isDomain={selected?.isDomainProperty ?? false}
          className="h-3.5 w-3.5 shrink-0 text-[#4285f4]"
        />
        <span
          className={cn(
            'min-w-0 flex-1 truncate',
            selected ? 'font-medium text-text' : 'text-text-faint',
          )}
        >
          {selected
            ? prettySiteLabel(selected.siteUrl)
            : credentialId
              ? 'Pick a Search Console site…'
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
                placeholder="Filter sites…"
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
            {!loading && !error && filtered && filtered.length === 0 && (
              <div className="px-3 py-6 text-center text-[11.5px] text-text-muted">
                {query
                  ? `No Search Console sites matching "${query}".`
                  : 'No verified Search Console sites for this Google account.'}
              </div>
            )}
            {!error && filtered && filtered.length > 0 && (
              <ul>
                {filtered.map((s) => {
                  const isSelected = selected?.siteUrl === s.siteUrl
                  const label = prettySiteLabel(s.siteUrl)
                  return (
                    <li key={s.siteUrl}>
                      <button
                        type="button"
                        onClick={() => pickAndClose(s)}
                        className={cn(
                          'flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px]',
                          'transition-colors hover:bg-surface-2',
                          isSelected && 'bg-surface-2',
                        )}
                      >
                        <SiteIcon
                          isDomain={s.isDomainProperty}
                          className="h-3.5 w-3.5 shrink-0 text-[#4285f4]"
                        />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-text" title={s.siteUrl}>
                            {label}
                          </div>
                          <div className="truncate text-[10.5px] text-text-faint">
                            {s.isDomainProperty ? 'Domain property' : 'URL prefix'}
                            {s.permissionLevel ? ` · ${s.permissionLevel}` : ''}
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
            )}
          </div>
        </div>
      )}
    </div>
  )
}

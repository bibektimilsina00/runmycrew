import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Check,
  ChevronDown,
  Database,
  Loader2,
  Search,
  X,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import { ApiErrorMessage } from './ApiErrorMessage'
import type { RendererProps } from '../types'

/**
 * Google Cloud Storage bucket picker — searchable dropdown listing
 * buckets in the GCP project named by the sibling `project_id` field.
 * The Storage API scopes bucket-list to one project at a time, so the
 * picker waits until that field is set before fetching.
 *
 * Stored value: bare bucket name string. Bucket names are globally
 * unique, so there's no need to keep `{id, name}` separately.
 */

interface BucketEntry {
  name: string
  location: string
  storageClass: string
  created: string
}

interface BucketsResponse {
  buckets: BucketEntry[]
}

function parseValue(v: unknown): string | null {
  if (typeof v === 'string') return v || null
  if (v && typeof v === 'object' && 'name' in v) {
    const obj = v as { name?: string }
    return typeof obj.name === 'string' && obj.name ? obj.name : null
  }
  return null
}

export function GCSBucketPickerRenderer({
  value,
  onChange,
  disabled,
  properties,
}: RendererProps) {
  const selected = parseValue(value)
  const credentialId =
    typeof properties?.credential === 'string' ? properties.credential : ''
  const projectId =
    typeof properties?.project_id === 'string' ? properties.project_id.trim() : ''

  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [items, setItems] = useState<BucketEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wrapRef = useRef<HTMLDivElement | null>(null)
  const searchRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!open || !credentialId || !projectId) return
    let alive = true
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)
    apiClient
      .get<BucketsResponse>(
        `/credentials/${credentialId}/gcs/buckets?project_id=${encodeURIComponent(projectId)}`,
      )
      .then(({ data }) => {
        if (!alive) return
        setItems(data.buckets || [])
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load buckets'
        setError(String(msg))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [open, credentialId, projectId])

  // Reset cached list when either sibling changes — the previous list
  // belongs to a different project.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setItems(null)
    setQuery('')
  }, [credentialId, projectId])

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

  const pickAndClose = (entry: BucketEntry) => {
    onChange(entry.name)
    setOpen(false)
    setQuery('')
  }

  const filtered = useMemo(() => {
    if (!items) return null
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter((b) => b.name.toLowerCase().includes(q))
  }, [items, query])

  const triggerDisabled = disabled || !credentialId || !projectId
  const tooltip = !credentialId
    ? 'Pick a Google account on this node first.'
    : !projectId
      ? 'Enter the Project ID first.'
      : undefined

  return (
    <div ref={wrapRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={triggerDisabled}
        title={tooltip}
        className={cn(
          'flex w-full items-center gap-2 rounded-[6px] border bg-surface px-2.5 py-1.5',
          'text-left text-[12px] transition-colors',
          open ? 'border-accent' : 'border-border-faint hover:border-text-faint',
          triggerDisabled && 'cursor-not-allowed opacity-50',
        )}
      >
        <Database className="h-3.5 w-3.5 shrink-0 text-[#4285f4]" />
        <span
          className={cn(
            'min-w-0 flex-1 truncate',
            selected ? 'font-medium text-text' : 'text-text-faint',
          )}
        >
          {selected
            ? selected
            : !credentialId
              ? 'Pick a Google account first'
              : !projectId
                ? 'Enter Project ID first'
                : 'Pick a bucket…'}
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

      {open && credentialId && projectId && (
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
                placeholder="Filter buckets…"
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
                  ? `No buckets matching "${query}".`
                  : `No buckets in project "${projectId}".`}
              </div>
            )}
            {!error && filtered && filtered.length > 0 && (
              <ul>
                {filtered.map((b) => {
                  const isSelected = selected === b.name
                  return (
                    <li key={b.name}>
                      <button
                        type="button"
                        onClick={() => pickAndClose(b)}
                        className={cn(
                          'flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px]',
                          'transition-colors hover:bg-surface-2',
                          isSelected && 'bg-surface-2',
                        )}
                      >
                        <Database className="h-3.5 w-3.5 shrink-0 text-[#4285f4]" />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-text" title={b.name}>
                            {b.name}
                          </div>
                          {(b.location || b.storageClass) && (
                            <div className="truncate text-[10.5px] text-text-faint">
                              {b.location}
                              {b.storageClass ? ` · ${b.storageClass}` : ''}
                            </div>
                          )}
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

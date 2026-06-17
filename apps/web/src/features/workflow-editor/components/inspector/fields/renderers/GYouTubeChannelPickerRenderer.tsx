import { useEffect, useRef, useState } from 'react'
import {
  Check,
  ChevronDown,
  Loader2,
  Search,
  User2,
  X,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import type { RendererProps } from '../types'

/**
 * YouTube channel picker — search-as-you-type backed by
 * `GET /credentials/{cid}/youtube/channels?query=…`. Accepts both
 * `@handle` lookups (resolved directly by the backend) and free-text
 * channel-name searches.
 *
 * Stored value: `{ id, title }`.
 */

interface PickerValue {
  id: string
  title: string
}

interface ChannelEntry {
  id: string
  title: string
  description?: string
  thumbnail_url?: string
  subscriber_count?: number
  handle?: string
}

interface ChannelsResponse {
  channels: ChannelEntry[]
}

function parseValue(v: unknown): PickerValue | null {
  if (typeof v === 'string') {
    if (!v) return null
    return { id: v, title: v }
  }
  if (v && typeof v === 'object' && 'id' in v) {
    const obj = v as { id?: string; title?: string; name?: string }
    if (typeof obj.id === 'string' && obj.id) {
      return { id: obj.id, title: obj.title || obj.name || obj.id }
    }
  }
  return null
}

function useDebounced<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value)
  const handle = useRef<number | undefined>(undefined)
  useEffect(() => {
    handle.current = window.setTimeout(() => setDebounced(value), ms)
    return () => {
      if (handle.current !== undefined) window.clearTimeout(handle.current)
    }
  }, [value, ms])
  return debounced
}

export function GYouTubeChannelPickerRenderer({
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
  const [items, setItems] = useState<ChannelEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wrapRef = useRef<HTMLDivElement | null>(null)
  const searchRef = useRef<HTMLInputElement | null>(null)

  // Channels API is search-only (no list-all). Debounce so we don't
  // hammer the search endpoint on every keystroke.
  const debouncedQuery = useDebounced(query.trim(), 350)

  useEffect(() => {
    if (!open || !credentialId || debouncedQuery.length < 2) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setItems(null)
      return
    }
    let alive = true
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)
    apiClient
      .get<ChannelsResponse>(
        `/credentials/${credentialId}/youtube/channels`,
        { params: { query: debouncedQuery } },
      )
      .then(({ data }) => {
        if (!alive) return
        setItems(data.channels)
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not search channels'
        setError(String(msg))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [open, credentialId, debouncedQuery])

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

  const pickAndClose = (entry: ChannelEntry) => {
    onChange({ id: entry.id, title: entry.title })
    setOpen(false)
    setQuery('')
  }

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
        <User2 className="h-3.5 w-3.5 shrink-0 text-[#ff0000]" />
        <span
          className={cn(
            'min-w-0 flex-1 truncate',
            selected ? 'font-medium text-text' : 'text-text-faint',
          )}
        >
          {selected
            ? selected.title
            : credentialId
              ? 'Search a channel by name or @handle…'
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
                placeholder="Name or @handle…"
                className={cn(
                  'h-7 w-full rounded-[5px] bg-surface pl-7 pr-2 text-[12px] text-text',
                  'outline-none placeholder:text-text-faint',
                  'focus:ring-1 focus:ring-accent',
                )}
              />
            </div>
          </div>

          <div className="max-h-[300px] overflow-y-auto">
            {!query.trim() && !items && (
              <div className="px-3 py-6 text-center text-[11.5px] text-text-muted">
                Start typing a channel name or @handle to search.
              </div>
            )}
            {loading && (
              <div className="flex items-center justify-center gap-2 py-6 text-[12px] text-text-muted">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Searching…
              </div>
            )}
            {error && !loading && (
              <div className="px-3 py-3 text-[12px] text-[var(--err,#dc2626)]">{error}</div>
            )}
            {!loading && !error && items && items.length === 0 && (
              <div className="px-3 py-6 text-center text-[11.5px] text-text-muted">
                No channels matching "{query}".
              </div>
            )}
            {!error && items && items.length > 0 && (
              <ul>
                {items.map((c) => {
                  const isSelected = selected?.id === c.id
                  return (
                    <li key={c.id}>
                      <button
                        type="button"
                        onClick={() => pickAndClose(c)}
                        className={cn(
                          'flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px]',
                          'transition-colors hover:bg-surface-2',
                          isSelected && 'bg-surface-2',
                        )}
                      >
                        {c.thumbnail_url ? (
                          <img
                            src={c.thumbnail_url}
                            alt=""
                            className="h-6 w-6 shrink-0 rounded-full object-cover"
                          />
                        ) : (
                          <User2 className="h-3.5 w-3.5 shrink-0 text-[#ff0000]" />
                        )}
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-text" title={c.title}>
                            {c.title}
                          </div>
                          {c.subscriber_count !== undefined && (
                            <div className="truncate text-[10px] text-text-faint">
                              {c.subscriber_count.toLocaleString()} subscribers
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

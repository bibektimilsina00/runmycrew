import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Check,
  ChevronDown,
  Hash,
  Loader2,
  MessageCircle,
  Search,
  Users,
  X,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import type { RendererProps } from '../types'

/**
 * Google Chat space picker — dropdown of the user's spaces, grouped
 * visually by type with a CEL filter forwarded to the API.
 *
 * Backend: `GET /credentials/{cid}/gchat/spaces?space_type=…`.
 *
 * Stored value: `{ id, name, displayName, type }`. The Pydantic side
 * normalises this down to the API resource path `spaces/{id}`; the
 * editor keeps the human-readable display name visible.
 *
 * Chat does not expose a generic `create space` flow that's safe to
 * invoke from a workflow editor (it would need admin / Workspace
 * Marketplace context), so there's no inline-create row here — pick
 * an existing space the user is already a member of.
 */

interface PickerValue {
  id: string
  name: string
  displayName: string
  type: string
}

interface SpaceEntry {
  id: string
  name: string
  displayName: string
  type: string
  singleUserBotDm?: boolean
}

interface SpacesResponse {
  spaces: SpaceEntry[]
  nextPageToken?: string
}

const TYPE_FILTERS: { label: string; value: string }[] = [
  { label: 'All', value: '' },
  { label: 'Rooms', value: 'SPACE' },
  { label: 'DMs', value: 'DIRECT_MESSAGE' },
  { label: 'Groups', value: 'GROUP_CHAT' },
]

function parseValue(v: unknown): PickerValue | null {
  if (typeof v === 'string') {
    if (!v) return null
    const id = v.startsWith('spaces/') ? v.slice('spaces/'.length) : v
    return { id, name: `spaces/${id}`, displayName: id, type: '' }
  }
  if (v && typeof v === 'object' && 'id' in v) {
    const obj = v as Partial<PickerValue> & { id?: string }
    if (typeof obj.id === 'string' && obj.id) {
      return {
        id: obj.id,
        name: obj.name || `spaces/${obj.id}`,
        displayName: obj.displayName || obj.id,
        type: obj.type || '',
      }
    }
  }
  return null
}

function SpaceIcon({
  type,
  className,
}: {
  type: string | undefined
  className?: string
}) {
  // Static JSX branches sidestep React-compiler "component created at
  // render time" warnings that fire if we route the lucide component
  // through a variable.
  if (type === 'DIRECT_MESSAGE') return <MessageCircle className={className} />
  if (type === 'GROUP_CHAT') return <Users className={className} />
  return <Hash className={className} />
}

export function GChatSpacePickerRenderer({
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
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [items, setItems] = useState<SpaceEntry[] | null>(null)
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
    const params = new URLSearchParams()
    if (typeFilter) params.set('space_type', typeFilter)
    apiClient
      .get<SpacesResponse>(
        `/credentials/${credentialId}/gchat/spaces?${params.toString()}`,
      )
      .then(({ data }) => {
        if (!alive) return
        setItems(data.spaces || [])
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load spaces'
        setError(String(msg))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [open, credentialId, typeFilter])

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

  const pickAndClose = (entry: SpaceEntry) => {
    onChange({
      id: entry.id,
      name: entry.name,
      displayName: entry.displayName || entry.id,
      type: entry.type,
    })
    setOpen(false)
    setQuery('')
  }

  const filtered = useMemo(() => {
    if (!items) return null
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter(
      (s) =>
        s.displayName.toLowerCase().includes(q) || s.id.toLowerCase().includes(q),
    )
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
        <SpaceIcon
          type={selected?.type}
          className="h-3.5 w-3.5 shrink-0 text-[#1a73e8]"
        />
        <span
          className={cn(
            'min-w-0 flex-1 truncate',
            selected ? 'font-medium text-text' : 'text-text-faint',
          )}
        >
          {selected
            ? selected.displayName
            : credentialId
              ? 'Pick a Chat space…'
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
                placeholder="Filter spaces…"
                className={cn(
                  'h-7 w-full rounded-[5px] bg-surface pl-7 pr-2 text-[12px] text-text',
                  'outline-none placeholder:text-text-faint',
                  'focus:ring-1 focus:ring-accent',
                )}
              />
            </div>
            <div className="mt-2 flex gap-1">
              {TYPE_FILTERS.map((f) => (
                <button
                  key={f.value || 'all'}
                  type="button"
                  onClick={() => setTypeFilter(f.value)}
                  className={cn(
                    'rounded-[5px] px-2 py-0.5 text-[10.5px] transition-colors',
                    typeFilter === f.value
                      ? 'bg-accent text-bg'
                      : 'bg-surface text-text-mute hover:bg-surface-2',
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          <div className="max-h-[300px] overflow-y-auto">
            {loading && !items && (
              <div className="flex items-center justify-center gap-2 py-6 text-[12px] text-text-muted">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Loading…
              </div>
            )}
            {error && !loading && (
              <div className="px-3 py-3 text-[12px] text-[var(--err,#dc2626)]">{error}</div>
            )}
            {!loading && !error && filtered && filtered.length === 0 && (
              <div className="px-3 py-6 text-center text-[11.5px] text-text-muted">
                {query
                  ? `No spaces matching "${query}".`
                  : 'No matching spaces — add the connected Google account to a space first.'}
              </div>
            )}
            {!error && filtered && filtered.length > 0 && (
              <ul>
                {filtered.map((space) => {
                  const isSelected = selected?.id === space.id
                  const label = space.displayName || space.id
                  return (
                    <li key={space.id}>
                      <button
                        type="button"
                        onClick={() => pickAndClose(space)}
                        className={cn(
                          'flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px]',
                          'transition-colors hover:bg-surface-2',
                          isSelected && 'bg-surface-2',
                        )}
                      >
                        <SpaceIcon
                          type={space.type}
                          className="h-3.5 w-3.5 shrink-0 text-[#1a73e8]"
                        />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-text" title={label}>
                            {label}
                          </div>
                          {space.type && (
                            <div className="truncate text-[10.5px] text-text-faint">
                              {space.type.replace('_', ' ').toLowerCase()}
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

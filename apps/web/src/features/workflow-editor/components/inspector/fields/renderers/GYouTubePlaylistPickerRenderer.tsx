import { useEffect, useRef, useState } from 'react'
import {
  Check,
  ChevronDown,
  ListVideo,
  Loader2,
  Plus,
  Search,
  X,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import type { RendererProps } from '../types'

/**
 * YouTube playlist picker — inline dropdown w/ inline "+ Create new"
 * CTA. Backed by `GET + POST /credentials/{cid}/youtube/playlists`.
 *
 * Stored value: `{ id, title }`. Pydantic accepts both shapes.
 */

interface PickerValue {
  id: string
  title: string
}

interface PlaylistEntry {
  id: string
  title: string
  description?: string
  item_count?: number
  privacy?: string
}

interface PlaylistsResponse {
  playlists: PlaylistEntry[]
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

export function GYouTubePlaylistPickerRenderer({
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
  const [items, setItems] = useState<PlaylistEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newTitle, setNewTitle] = useState('')
  const [creating, setCreating] = useState(false)
  const [createErr, setCreateErr] = useState<string | null>(null)

  const wrapRef = useRef<HTMLDivElement | null>(null)
  const searchRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!open || !credentialId) return
    let alive = true
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)
    apiClient
      .get<PlaylistsResponse>(`/credentials/${credentialId}/youtube/playlists`)
      .then(({ data }) => {
        if (!alive) return
        setItems(data.playlists)
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load playlists'
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
    setNewTitle('')
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

  const handleCreate = async () => {
    const title = newTitle.trim()
    if (!title || !credentialId) return
    setCreateErr(null)
    setCreating(true)
    try {
      const { data } = await apiClient.post<PlaylistEntry>(
        `/credentials/${credentialId}/youtube/playlists`,
        { title, privacy: 'private' },
      )
      onChange({ id: data.id, title: data.title })
      setOpen(false)
      setNewTitle('')
      setItems((prev) =>
        prev
          ? [
              { id: data.id, title: data.title, privacy: data.privacy },
              ...prev.filter((p) => p.id !== data.id),
            ]
          : prev,
      )
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setCreateErr(err.response?.data?.detail || err.message || 'Create failed')
    } finally {
      setCreating(false)
    }
  }

  const pickAndClose = (entry: PlaylistEntry) => {
    onChange({ id: entry.id, title: entry.title })
    setOpen(false)
    setQuery('')
  }

  const q = query.trim().toLowerCase()
  const filtered = items?.filter((p) => !q || p.title.toLowerCase().includes(q)) ?? null

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
        <ListVideo className="h-3.5 w-3.5 shrink-0 text-[#ff0000]" />
        <span
          className={cn(
            'min-w-0 flex-1 truncate',
            selected ? 'font-medium text-text' : 'text-text-faint',
          )}
        >
          {selected
            ? selected.title
            : credentialId
              ? 'Pick a playlist…'
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
                placeholder="Filter playlists…"
                className={cn(
                  'h-7 w-full rounded-[5px] bg-surface pl-7 pr-2 text-[12px] text-text',
                  'outline-none placeholder:text-text-faint',
                  'focus:ring-1 focus:ring-accent',
                )}
              />
            </div>
          </div>

          <div className="border-b border-border-faint bg-surface/40 px-2 py-1.5">
            <div className="flex items-center gap-1.5">
              <Plus className="h-3 w-3 shrink-0 text-accent" />
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    void handleCreate()
                  }
                }}
                placeholder="Create new playlist…"
                className={cn(
                  'h-6 flex-1 bg-transparent text-[12px] text-text outline-none',
                  'placeholder:text-text-faint',
                )}
              />
              <button
                type="button"
                onClick={() => void handleCreate()}
                disabled={creating || !newTitle.trim()}
                className={cn(
                  'rounded-[4px] px-2 py-0.5 text-[10.5px] font-medium transition-colors',
                  'bg-accent text-bg hover:opacity-90',
                  (creating || !newTitle.trim()) && 'cursor-not-allowed opacity-50',
                )}
              >
                {creating ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Create'}
              </button>
            </div>
            {createErr && (
              <div
                className="mt-1 text-[10.5px] text-[var(--err,#dc2626)]"
                title={createErr}
              >
                {createErr}
              </div>
            )}
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
                {q
                  ? `No playlists matching "${query}".`
                  : 'No playlists yet — create one above.'}
              </div>
            )}
            {!error && filtered && filtered.length > 0 && (
              <ul>
                {filtered.map((p) => {
                  const isSelected = selected?.id === p.id
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
                        <ListVideo className="h-3.5 w-3.5 shrink-0 text-[#ff0000]" />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-text" title={p.title}>
                            {p.title}
                          </div>
                          {p.item_count !== undefined && (
                            <div className="truncate text-[10px] text-text-faint">
                              {p.item_count} {p.item_count === 1 ? 'video' : 'videos'}
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

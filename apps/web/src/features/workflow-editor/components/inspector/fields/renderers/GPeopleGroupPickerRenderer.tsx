import { useEffect, useRef, useState } from 'react'
import {
  Check,
  ChevronDown,
  Loader2,
  Plus,
  Search,
  Tag,
  X,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import type { RendererProps } from '../types'

/**
 * Google Contacts (People API) contact-group picker — same UX shape
 * as the gtasks tasklist picker: inline dropdown that auto-loads when
 * a credential is set, with an inline "+ Create new group" CTA.
 *
 * Stored value: `{ resourceName, name }`. The Pydantic validator on
 * the runtime side accepts both the dict shape and a bare resource
 * name string, so existing graphs keep working.
 *
 * Backend endpoints:
 *   GET  /credentials/{cid}/gpeople/groups
 *   POST /credentials/{cid}/gpeople/groups  body:{name}
 */

interface PickerValue {
  resourceName: string
  name: string
}

interface GroupEntry {
  resource_name: string
  name: string
  member_count?: number
  type?: string
}

interface GroupsResponse {
  groups: GroupEntry[]
}

function parseValue(v: unknown): PickerValue | null {
  if (typeof v === 'string') {
    if (!v) return null
    return { resourceName: v, name: v }
  }
  if (v && typeof v === 'object') {
    const obj = v as {
      resourceName?: string
      id?: string
      name?: string
      title?: string
    }
    const rn = obj.resourceName || obj.id
    if (typeof rn === 'string' && rn) {
      return { resourceName: rn, name: obj.name || obj.title || rn }
    }
  }
  return null
}

export function GPeopleGroupPickerRenderer({
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
  const [items, setItems] = useState<GroupEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
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
      .get<GroupsResponse>(`/credentials/${credentialId}/gpeople/groups`)
      .then(({ data }) => {
        if (!alive) return
        setItems(data.groups)
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load groups'
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
    setNewName('')
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
    const name = newName.trim()
    if (!name || !credentialId) return
    setCreateErr(null)
    setCreating(true)
    try {
      const { data } = await apiClient.post<GroupEntry>(
        `/credentials/${credentialId}/gpeople/groups`,
        { name },
      )
      onChange({ resourceName: data.resource_name, name: data.name })
      setOpen(false)
      setNewName('')
      setItems((prev) =>
        prev
          ? [
              { resource_name: data.resource_name, name: data.name },
              ...prev.filter((g) => g.resource_name !== data.resource_name),
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

  const pickAndClose = (entry: GroupEntry) => {
    onChange({ resourceName: entry.resource_name, name: entry.name })
    setOpen(false)
    setQuery('')
  }

  const q = query.trim().toLowerCase()
  const filtered = items?.filter((g) => !q || g.name.toLowerCase().includes(q)) ?? null

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
        <Tag className="h-3.5 w-3.5 shrink-0 text-[#1a73e8]" />
        <span
          className={cn(
            'min-w-0 flex-1 truncate',
            selected ? 'font-medium text-text' : 'text-text-faint',
          )}
        >
          {selected
            ? selected.name
            : credentialId
              ? 'Pick a group…'
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
                placeholder="Filter groups…"
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
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    void handleCreate()
                  }
                }}
                placeholder="Create new group…"
                className={cn(
                  'h-6 flex-1 bg-transparent text-[12px] text-text outline-none',
                  'placeholder:text-text-faint',
                )}
              />
              <button
                type="button"
                onClick={() => void handleCreate()}
                disabled={creating || !newName.trim()}
                className={cn(
                  'rounded-[4px] px-2 py-0.5 text-[10.5px] font-medium transition-colors',
                  'bg-accent text-bg hover:opacity-90',
                  (creating || !newName.trim()) && 'cursor-not-allowed opacity-50',
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
                  ? `No groups matching "${query}".`
                  : 'No groups yet — create one above.'}
              </div>
            )}
            {!error && filtered && filtered.length > 0 && (
              <ul>
                {filtered.map((g) => {
                  const isSelected = selected?.resourceName === g.resource_name
                  return (
                    <li key={g.resource_name}>
                      <button
                        type="button"
                        onClick={() => pickAndClose(g)}
                        className={cn(
                          'flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px]',
                          'transition-colors hover:bg-surface-2',
                          isSelected && 'bg-surface-2',
                        )}
                      >
                        <Tag className="h-3.5 w-3.5 shrink-0 text-[#1a73e8]" />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-text" title={g.name}>
                            {g.name}
                          </div>
                          {g.member_count !== undefined && (
                            <div className="truncate text-[10px] text-text-faint">
                              {g.member_count} {g.member_count === 1 ? 'member' : 'members'}
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

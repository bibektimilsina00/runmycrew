import { useEffect, useRef, useState } from 'react'
import {
  Check,
  ChevronDown,
  ClipboardList,
  FileSpreadsheet,
  FileText,
  Folder,
  Loader2,
  Plus,
  Presentation,
  Search,
  X,
  type LucideIcon,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import type { RendererProps } from '../types'

/**
 * Generic Google file picker — works for any Google-native mime type.
 * One inline searchable dropdown auto-loads the user's files of the
 * requested mime as soon as a credential is set. A "Create new" row at
 * the top calls the backend's generic create endpoint, which routes to
 * the right native API (Sheets / Docs / Slides / …).
 *
 * typeOptions:
 *   - `mimeType` (required) — Google-native MIME of the files to list.
 *   - `placeholder`         — empty-state label (default: "Pick a file…").
 *   - `createPlaceholder`   — placeholder for the create-new input
 *                             (default: "Create new…").
 *   - `searchPlaceholder`   — search input placeholder
 *                             (default: "Search…").
 *   - `disableCreate`       — true → hide the inline create row (use
 *                             for mime types whose API can't create).
 *
 * Stored value: `{ id, name }`. Pydantic on the runtime side accepts
 * both the dict shape and a bare string id so existing graphs work.
 *
 * Backend endpoints:
 *   GET  /credentials/{cid}/google-files?mime_type=…&query=…
 *   POST /credentials/{cid}/google-files  body:{mime_type, title}
 */

interface PickerValue {
  id: string
  name: string
}

interface FileEntry {
  id: string
  name: string
  modifiedTime?: string
  webViewLink?: string
}

interface FilesResponse {
  files: FileEntry[]
}

interface CreateResponse {
  id: string
  name: string
  webViewLink?: string
}

// Well-known Google mime types get a friendly icon + accent colour.
// Unknown mimes fall back to a generic file icon.
const MIME_LOOKS: Record<string, { Icon: LucideIcon; color: string }> = {
  'application/vnd.google-apps.spreadsheet': {
    Icon: FileSpreadsheet,
    color: '#0f9d58',
  },
  'application/vnd.google-apps.document': {
    Icon: FileText,
    color: '#4285f4',
  },
  'application/vnd.google-apps.presentation': {
    Icon: Presentation,
    color: '#f4b400',
  },
  'application/vnd.google-apps.folder': {
    Icon: Folder,
    color: '#80868b',
  },
  'application/vnd.google-apps.form': {
    Icon: ClipboardList,
    color: '#673ab7',
  },
}

function looksForMime(mime: string): { Icon: LucideIcon; color: string } {
  return MIME_LOOKS[mime] || { Icon: FileText, color: 'currentColor' }
}

function parseValue(v: unknown): PickerValue | null {
  if (typeof v === 'string') {
    if (!v) return null
    return { id: v, name: v }
  }
  if (v && typeof v === 'object' && 'id' in v) {
    const obj = v as { id?: string; name?: string }
    if (typeof obj.id === 'string' && obj.id) {
      return { id: obj.id, name: obj.name || obj.id }
    }
  }
  return null
}

export function GoogleFilePickerRenderer({
  prop,
  value,
  onChange,
  disabled,
  properties,
}: RendererProps) {
  const opts = (prop.typeOptions ?? {}) as Record<string, unknown>
  const mimeType = typeof opts.mimeType === 'string' ? opts.mimeType : ''
  const placeholder =
    typeof opts.placeholder === 'string' ? opts.placeholder : 'Pick a file…'
  const createPlaceholder =
    typeof opts.createPlaceholder === 'string'
      ? opts.createPlaceholder
      : 'Create new…'
  const searchPlaceholder =
    typeof opts.searchPlaceholder === 'string'
      ? opts.searchPlaceholder
      : 'Search…'
  const disableCreate = opts.disableCreate === true

  const selected = parseValue(value)
  const credentialId =
    typeof properties?.credential === 'string' ? properties.credential : ''

  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [items, setItems] = useState<FileEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [createErr, setCreateErr] = useState<string | null>(null)

  const wrapRef = useRef<HTMLDivElement | null>(null)
  const searchRef = useRef<HTMLInputElement | null>(null)

  const debouncedQuery = useDebounced(query, 250)
  const { Icon, color } = looksForMime(mimeType)

  useEffect(() => {
    if (!open || !credentialId || !mimeType) return
    let alive = true
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    setError(null)
    apiClient
      .get<FilesResponse>(`/credentials/${credentialId}/google-files`, {
        params: {
          mime_type: mimeType,
          query: debouncedQuery,
          page_size: 100,
        },
      })
      .then(({ data }) => {
        if (!alive) return
        setItems(data.files)
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load files'
        setError(String(msg))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [open, credentialId, mimeType, debouncedQuery])

  // Reset cached state when the credential changes — list belongs to
  // the previous account.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setItems(null)
    setQuery('')
    setCreating(false)
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
    if (open && !creating) searchRef.current?.focus()
  }, [open, creating])

  const handleCreate = async () => {
    const t = newTitle.trim()
    if (!t || !credentialId || !mimeType) return
    setCreateErr(null)
    setCreating(true)
    try {
      const { data } = await apiClient.post<CreateResponse>(
        `/credentials/${credentialId}/google-files`,
        { mime_type: mimeType, title: t },
      )
      onChange({ id: data.id, name: data.name })
      setOpen(false)
      setNewTitle('')
      // Prepend optimistically so the next reopen shows the new file
      // even if the list query is still in flight.
      setItems((prev) =>
        prev
          ? [{ id: data.id, name: data.name }, ...prev.filter((s) => s.id !== data.id)]
          : prev,
      )
    } catch (e) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setCreateErr(err.response?.data?.detail || err.message || 'Create failed')
    } finally {
      setCreating(false)
    }
  }

  const pickAndClose = (file: { id: string; name: string }) => {
    onChange({ id: file.id, name: file.name })
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
        <Icon className="h-3.5 w-3.5 shrink-0" style={{ color }} />
        <span
          className={cn(
            'min-w-0 flex-1 truncate',
            selected ? 'font-medium text-text' : 'text-text-faint',
          )}
        >
          {selected
            ? selected.name
            : credentialId
              ? placeholder
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
                placeholder={searchPlaceholder}
                className={cn(
                  'h-7 w-full rounded-[5px] bg-surface pl-7 pr-2 text-[12px] text-text',
                  'outline-none placeholder:text-text-faint',
                  'focus:ring-1 focus:ring-accent',
                )}
              />
            </div>
          </div>

          {!disableCreate && (
            <CreateRow
              title={newTitle}
              placeholder={createPlaceholder}
              onTitleChange={setNewTitle}
              onSubmit={handleCreate}
              creating={creating}
              error={createErr}
            />
          )}

          <div className="max-h-[300px] overflow-y-auto">
            {loading && !items && (
              <div className="flex items-center justify-center gap-2 py-6 text-[12px] text-text-muted">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Loading…
              </div>
            )}
            {error && !loading && (
              <div className="px-3 py-3 text-[12px] text-[var(--err,#dc2626)]">
                {error}
              </div>
            )}
            {!loading && !error && items && items.length === 0 && (
              <div className="px-3 py-6 text-center text-[11.5px] text-text-muted">
                {query
                  ? `No files matching "${query}".`
                  : disableCreate
                    ? 'No files found.'
                    : 'No files yet — create one above.'}
              </div>
            )}
            {!error && items && items.length > 0 && (
              <ul>
                {items.map((file) => {
                  const isSelected = selected?.id === file.id
                  return (
                    <li key={file.id}>
                      <button
                        type="button"
                        onClick={() => pickAndClose(file)}
                        className={cn(
                          'flex w-full items-center gap-2 px-3 py-1.5 text-left text-[12px]',
                          'transition-colors hover:bg-surface-2',
                          isSelected && 'bg-surface-2',
                        )}
                      >
                        <Icon
                          className="h-3.5 w-3.5 shrink-0"
                          style={{ color }}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-text" title={file.name}>
                            {file.name}
                          </div>
                          {file.modifiedTime && (
                            <div className="truncate text-[10px] text-text-faint">
                              Modified {formatDate(file.modifiedTime)}
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

function CreateRow({
  title,
  placeholder,
  onTitleChange,
  onSubmit,
  creating,
  error,
}: {
  title: string
  placeholder: string
  onTitleChange: (v: string) => void
  onSubmit: () => void
  creating: boolean
  error: string | null
}) {
  return (
    <div className="border-b border-border-faint bg-surface/40 px-2 py-1.5">
      <div className="flex items-center gap-1.5">
        <Plus className="h-3 w-3 shrink-0 text-accent" />
        <input
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault()
              onSubmit()
            }
          }}
          placeholder={placeholder}
          className={cn(
            'h-6 flex-1 bg-transparent text-[12px] text-text outline-none',
            'placeholder:text-text-faint',
          )}
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={creating || !title.trim()}
          className={cn(
            'rounded-[4px] px-2 py-0.5 text-[10.5px] font-medium transition-colors',
            'bg-accent text-bg hover:opacity-90',
            (creating || !title.trim()) && 'cursor-not-allowed opacity-50',
          )}
        >
          {creating ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Create'}
        </button>
      </div>
      {error && (
        <div
          className="mt-1 text-[10.5px] text-[var(--err,#dc2626)]"
          title={error}
        >
          {error}
        </div>
      )}
    </div>
  )
}

// ── helpers ──────────────────────────────────────────────────────────────

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

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

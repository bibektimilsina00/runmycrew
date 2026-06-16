import { useEffect, useState } from 'react'
import { ChevronRight, Folder, FolderOpen, Loader2 } from 'lucide-react'
import type { RendererProps } from '../types'
import { Modal, Button } from '@/shared/components'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'

/**
 * Google Drive folder selector — server-proxied, no SDK.
 *
 * The earlier version used Google's Picker SDK from `apis.google.com`,
 * which uBlock / AdGuard / Brave shields silently block for a chunk of
 * users. Adblockers operate at the network layer below the page —
 * unfixable from app code.
 *
 * This implementation skips the SDK entirely. The browser asks Fuse's
 * backend (`/credentials/{id}/drive/folders?parent_id=…`) for folders
 * under a given parent; backend calls Drive's `files.list` server-side
 * and returns just `{ id, name, has_children }`. UI renders a finder-
 * style browser with breadcrumbs. No `apis.google.com`, no third-party
 * JS, invisible to adblockers.
 *
 * Scope-wise this is purely a UX device — Drive access still flows
 * through OAuth (`drive.file` default, `drive.readonly` when
 * GOOGLE_DRIVE_WATCH_EXTERNAL is on). The browser doesn't grant
 * anything; it just lists what the credential can already see.
 */

interface PickerValue {
  id: string
  name: string
}

interface FolderEntry {
  id: string
  name: string
  has_children: boolean
}

interface FolderListResponse {
  parent: { id: string; name: string }
  folders: FolderEntry[]
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

export function GDrivePickerRenderer({ value, onChange, disabled, properties }: RendererProps) {
  const selected = parseValue(value)
  const [open, setOpen] = useState(false)

  const credentialId =
    typeof properties?.credential === 'string' ? properties.credential : ''

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setOpen(true)}
          disabled={disabled || !credentialId}
          title={!credentialId ? 'Pick a Google account on this node first.' : undefined}
          className={cn(
            'inline-flex items-center gap-1.5 h-8 px-3 rounded-[5px] text-xs font-medium',
            'border border-border bg-surface hover:bg-surface-2 text-text',
            'transition-colors',
            (disabled || !credentialId) && 'opacity-50 cursor-not-allowed',
          )}
        >
          <Folder className="h-3.5 w-3.5" />
          {selected ? 'Change folder' : 'Pick folder'}
        </button>
        {selected && (
          <div className="min-w-0 flex-1 truncate text-xs">
            <span className="font-medium text-text">{selected.name}</span>
            <span className="ml-1.5 font-mono text-[10.5px] text-text-muted">
              {selected.id.slice(0, 10)}…
            </span>
          </div>
        )}
        {selected && (
          <button
            type="button"
            onClick={() => onChange('')}
            disabled={disabled}
            className="text-[11px] text-text-muted hover:text-text"
            title="Clear selection"
          >
            Clear
          </button>
        )}
      </div>

      {open && credentialId && (
        <FolderBrowser
          credentialId={credentialId}
          onSelect={(picked) => {
            onChange({ id: picked.id, name: picked.name })
            setOpen(false)
          }}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  )
}

// ── modal ────────────────────────────────────────────────────────────────

interface BreadcrumbEntry {
  id: string
  name: string
}

function FolderBrowser({
  credentialId,
  onSelect,
  onClose,
}: {
  credentialId: string
  onSelect: (folder: BreadcrumbEntry) => void
  onClose: () => void
}) {
  const [stack, setStack] = useState<BreadcrumbEntry[]>([
    { id: 'root', name: 'My Drive' },
  ])
  const current = stack[stack.length - 1]
  const [folders, setFolders] = useState<FolderEntry[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let alive = true
    // Resetting state on parent navigation is the whole point of the
    // effect — eslint's set-state-in-effect rule doesn't fit here.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setError(null)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setFolders(null)
    apiClient
      .get<FolderListResponse>(
        `/credentials/${credentialId}/drive/folders`,
        { params: { parent_id: current.id } },
      )
      .then(({ data }) => {
        if (!alive) return
        if (data.parent?.name && data.parent.name !== current.name) {
          setStack((s) =>
            s.map((e, i) => (i === s.length - 1 ? { ...e, name: data.parent.name } : e)),
          )
        }
        setFolders(data.folders)
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load folders'
        setError(String(msg))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [credentialId, current.id, current.name])

  const goTo = (idx: number) => {
    setStack((s) => s.slice(0, idx + 1))
  }
  const open = (folder: FolderEntry) => {
    if (!folder.has_children) return
    setStack((s) => [...s, { id: folder.id, name: folder.name }])
  }

  const footer = (
    <>
      <Button variant="ghost" onClick={onClose}>
        Cancel
      </Button>
      <Button
        onClick={() => onSelect(current)}
        disabled={current.id === 'root'}
        title={
          current.id === 'root'
            ? 'Navigate into a folder before selecting it.'
            : `Select ${current.name}`
        }
      >
        Select this folder
      </Button>
    </>
  )

  return (
    <Modal
      open
      onClose={onClose}
      title="Pick a Google Drive folder"
      description="Navigate to the folder you want to watch and click Select."
      width="540px"
      footer={footer}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-1 text-[12px]">
          {stack.map((entry, idx) => (
            <span key={`${entry.id}-${idx}`} className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => goTo(idx)}
                className={cn(
                  'truncate max-w-[160px] px-1 rounded',
                  idx === stack.length - 1
                    ? 'text-text font-medium'
                    : 'text-text-muted hover:text-text hover:bg-surface-2',
                )}
              >
                {entry.name}
              </button>
              {idx < stack.length - 1 && (
                <ChevronRight className="h-3 w-3 text-text-faint shrink-0" />
              )}
            </span>
          ))}
        </div>

        <div className="min-h-[260px] max-h-[360px] overflow-y-auto rounded-[6px] border border-border-faint bg-bg">
          {loading && (
            <div className="flex h-full items-center justify-center gap-2 py-12 text-[12px] text-text-muted">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Loading folders…
            </div>
          )}
          {error && !loading && (
            <div className="px-3 py-4 text-[12px] text-[var(--danger,#dc2626)]">
              {error}
            </div>
          )}
          {!loading && !error && folders && folders.length === 0 && (
            <div className="px-3 py-8 text-center text-[12px] text-text-muted">
              No folders inside <span className="font-medium">{current.name}</span>.
              You can still select this folder.
            </div>
          )}
          {!loading && !error && folders && folders.length > 0 && (
            <ul className="divide-y divide-border-faint">
              {folders.map((folder) => (
                <li
                  key={folder.id}
                  className={cn(
                    'group flex items-center gap-2.5 px-3 py-2 text-[12.5px]',
                    'hover:bg-surface-2',
                  )}
                >
                  {folder.has_children ? (
                    <FolderOpen className="h-4 w-4 text-text-muted shrink-0" />
                  ) : (
                    <Folder className="h-4 w-4 text-text-faint shrink-0" />
                  )}
                  <span className="truncate flex-1 text-text">{folder.name}</span>
                  <button
                    type="button"
                    onClick={() => onSelect({ id: folder.id, name: folder.name })}
                    className={cn(
                      'rounded-[4px] px-2 py-0.5 text-[10.5px] font-medium',
                      'border border-border-faint text-text-muted',
                      'opacity-0 group-hover:opacity-100',
                      'hover:bg-accent hover:border-accent hover:text-bg',
                      'transition-opacity',
                    )}
                  >
                    Select
                  </button>
                  {folder.has_children && (
                    <button
                      type="button"
                      onClick={() => open(folder)}
                      className={cn(
                        'flex h-6 w-6 items-center justify-center rounded-[4px]',
                        'text-text-faint hover:bg-surface hover:text-text',
                      )}
                      title="Open"
                    >
                      <ChevronRight className="h-3.5 w-3.5" />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </Modal>
  )
}

import { useEffect, useMemo, useRef, useState } from 'react'
import {
  FileText,
  Image as ImageIcon,
  Loader2,
  Upload,
  X,
} from 'lucide-react'
import { z } from 'zod'
import { cn } from '@/lib/cn'
import { Modal, Button } from '@/shared/components'
import { requestJson } from '@/shared/utils/apiClient'
import apiClient from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import type { RendererProps } from '../types'

/**
 * Field renderer for `type: "media"` properties.
 *
 * Single unified input — paste a URL, drag-drop a file, or pick from the
 * asset library via the trailing icons. No tabs, no separate panes.
 *
 * Saves a discriminated union into node props so the backend can tell URL
 * input apart from a referenced Asset:
 *
 *   { type: "url",   value: "https://..." }
 *   { type: "asset", asset_id: "<uuid>", name: "...", mime: "image/jpeg" }
 *
 * typeOptions:
 *   - `accept`         — MIME filter (default `image/*,video/*`)
 *   - `mediaKindField` — sibling prop to set with `IMAGE` | `VIDEO` from mime
 *   - `nameField`      — sibling prop to autofill with the picked file's
 *                        name (only when currently blank — never clobbers
 *                        a user-typed value)
 */

const ASSET_OUT_SCHEMA = z.object({
  id: z.string(),
  name: z.string(),
  file_type: z.string(),
  file_size: z.number(),
  source_type: z.string(),
  url: z.string(),
  preview_url: z.string(),
  created_at: z.string(),
})

const ASSET_LIST_SCHEMA = z.array(ASSET_OUT_SCHEMA)

type MediaValue =
  | { type: 'url'; value: string }
  | { type: 'asset'; asset_id: string; name?: string; mime?: string }

type Asset = z.infer<typeof ASSET_OUT_SCHEMA>

function normalize(raw: unknown): MediaValue {
  if (raw === null || raw === undefined) return { type: 'url', value: '' }
  if (typeof raw === 'string') return { type: 'url', value: raw }
  if (typeof raw !== 'object') return { type: 'url', value: '' }
  const obj = raw as Record<string, unknown>
  if (obj.type === 'asset' && typeof obj.asset_id === 'string') {
    return {
      type: 'asset',
      asset_id: obj.asset_id,
      name: typeof obj.name === 'string' ? obj.name : undefined,
      mime: typeof obj.mime === 'string' ? obj.mime : undefined,
    }
  }
  if (obj.type === 'url') {
    const value = typeof obj.value === 'string' ? obj.value : ''
    return { type: 'url', value }
  }
  return { type: 'url', value: '' }
}

function isImageMime(mime?: string) {
  return !!mime && mime.startsWith('image/')
}

export function MediaRenderer({
  prop,
  value,
  properties,
  onChange,
  onPropertiesChange,
  disabled,
}: RendererProps) {
  const opts = (prop.typeOptions ?? {}) as Record<string, unknown>
  const accept = typeof opts.accept === 'string' ? opts.accept : 'image/*,video/*'
  const mediaKindField =
    typeof opts.mediaKindField === 'string' ? opts.mediaKindField : null
  const nameField = typeof opts.nameField === 'string' ? opts.nameField : null

  const current = useMemo(() => normalize(value), [value])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [libraryOpen, setLibraryOpen] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement | null>(null)
  const dragDepth = useRef(0)

  const kindFromMime = (mime: string | undefined): string | null => {
    if (!mediaKindField || !mime) return null
    if (mime.startsWith('image/')) return 'IMAGE'
    if (mime === 'video/quicktime') return 'VIDEO'
    if (mime.startsWith('video/')) return 'VIDEO'
    return null
  }

  const writeAsset = (asset: Pick<Asset, 'id' | 'name' | 'file_type'>) => {
    const next: MediaValue = {
      type: 'asset',
      asset_id: asset.id,
      name: asset.name,
      mime: asset.file_type,
    }
    const patch: Record<string, unknown> = { [prop.name]: next }
    const kind = kindFromMime(asset.file_type)
    if (kind && mediaKindField) patch[mediaKindField] = kind
    if (nameField) {
      const existing = properties?.[nameField]
      const blank =
        existing === undefined ||
        existing === null ||
        (typeof existing === 'string' && existing.trim() === '')
      if (blank) patch[nameField] = asset.name
    }
    if (Object.keys(patch).length > 1 && onPropertiesChange) {
      onPropertiesChange(patch)
    } else {
      onChange(next)
    }
  }

  const handleUpload = async (file: File) => {
    setUploadError(null)
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await apiClient.post(API_ROUTES.ASSET_UPLOAD, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const parsed = ASSET_OUT_SCHEMA.parse(res.data)
      writeAsset(parsed)
    } catch (e) {
      const err = e as { detail?: string; message?: string }
      setUploadError(err.detail || err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const onDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    if (!e.dataTransfer.types.includes('Files')) return
    dragDepth.current += 1
    setDragOver(true)
  }
  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    dragDepth.current = Math.max(0, dragDepth.current - 1)
    if (dragDepth.current === 0) setDragOver(false)
  }
  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    dragDepth.current = 0
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) void handleUpload(f)
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
        onDragOver={onDragOver}
        onDrop={onDrop}
        className={cn(
          'group relative flex items-center gap-1 rounded-[8px] border bg-surface',
          'transition-colors',
          dragOver
            ? 'border-accent bg-accent/5'
            : 'border-border-faint hover:border-text-faint focus-within:border-accent',
          disabled && 'opacity-50 pointer-events-none',
        )}
      >
        {current.type === 'asset' ? (
          <div className="flex min-w-0 flex-1 items-center gap-2 px-2 py-1.5">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[5px] bg-surface-2">
              {isImageMime(current.mime) ? (
                <ImageIcon className="h-3.5 w-3.5 text-text-mute" />
              ) : (
                <FileText className="h-3.5 w-3.5 text-text-mute" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div
                className="truncate text-[12px] font-medium text-text"
                title={current.name}
              >
                {current.name || current.asset_id}
              </div>
              {current.mime && (
                <div className="truncate font-mono text-[10px] text-text-faint">
                  {current.mime}
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={() => onChange({ type: 'url', value: '' })}
              className="rounded-[4px] p-1 text-text-faint hover:bg-surface-2 hover:text-text"
              title="Remove"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <input
            type="text"
            value={current.value}
            onChange={(e) => onChange({ type: 'url', value: e.target.value })}
            placeholder={prop.placeholder || 'Paste a URL or drop a file here'}
            disabled={disabled || uploading}
            className={cn(
              'flex-1 min-w-0 bg-transparent px-2.5 py-1.5 text-[12px] outline-none',
              'placeholder:text-text-faint',
            )}
          />
        )}

        <div className="flex shrink-0 items-center gap-0.5 pr-1">
          <IconBtn
            title="Upload from your computer"
            onClick={() => fileRef.current?.click()}
            disabled={disabled || uploading}
            icon={
              uploading ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" />
              ) : (
                <Upload className="h-3.5 w-3.5" />
              )
            }
          />
          <IconBtn
            title="Pick from library"
            onClick={() => setLibraryOpen(true)}
            disabled={disabled}
            icon={<ImageIcon className="h-3.5 w-3.5" />}
          />
        </div>

        <input
          ref={fileRef}
          type="file"
          accept={accept}
          className="hidden"
          disabled={disabled}
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) void handleUpload(f)
            e.target.value = ''
          }}
        />

        {dragOver && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center rounded-[8px] bg-accent/10 text-[12px] font-medium text-accent">
            Drop to upload
          </div>
        )}
      </div>

      {uploadError && (
        <div className="text-[11px] text-[var(--err)]">{uploadError}</div>
      )}

      {libraryOpen && (
        <LibraryModal
          accept={accept}
          selectedId={current.type === 'asset' ? current.asset_id : null}
          onPick={(asset) => {
            writeAsset(asset)
            setLibraryOpen(false)
          }}
          onClose={() => setLibraryOpen(false)}
        />
      )}
    </div>
  )
}

function IconBtn({
  icon,
  title,
  onClick,
  disabled,
}: {
  icon: React.ReactNode
  title: string
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={cn(
        'flex h-6 w-6 items-center justify-center rounded-[5px]',
        'text-text-mute hover:bg-surface-2 hover:text-text',
        'transition-colors',
        disabled && 'cursor-not-allowed opacity-50',
      )}
    >
      {icon}
    </button>
  )
}

function LibraryModal({
  accept,
  selectedId,
  onPick,
  onClose,
}: {
  accept: string
  selectedId: string | null
  onPick: (asset: Asset) => void
  onClose: () => void
}) {
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    requestJson(ASSET_LIST_SCHEMA, { url: API_ROUTES.ASSETS, method: 'GET' })
      .then((data) => {
        if (!alive) return
        setAssets(data)
        setError(null)
      })
      .catch((e: { detail?: string; message?: string }) => {
        if (!alive) return
        setError(e.detail || e.message || 'Failed to load library')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [])

  const filtered = useMemo(() => {
    const acceptParts = accept
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)
    if (acceptParts.length === 0 || acceptParts.includes('*/*')) return assets
    return assets.filter((a) => {
      const mime = a.file_type.toLowerCase()
      return acceptParts.some((p) => {
        if (p === '*/*') return true
        if (p.endsWith('/*')) return mime.startsWith(p.slice(0, -1))
        return mime === p
      })
    })
  }, [assets, accept])

  return (
    <Modal
      open
      onClose={onClose}
      title="Choose from library"
      width="640px"
      footer={
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
      }
    >
      <div className="px-6 py-4">
        {loading && (
          <div className="flex items-center justify-center gap-2 py-16 text-[12px] text-text-mute">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading library…
          </div>
        )}
        {error && !loading && (
          <div className="rounded-[6px] border border-[var(--err)] bg-[var(--err)]/5 px-3 py-2 text-[12px] text-[var(--err)]">
            {error}
          </div>
        )}
        {!loading && !error && filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
            <ImageIcon className="h-8 w-8 text-text-faint" />
            <div className="text-[13px] font-medium text-text">
              No files in your library
            </div>
            <div className="text-[11.5px] text-text-mute">
              Upload one from the field above to add it here.
            </div>
          </div>
        )}
        {!loading && !error && filtered.length > 0 && (
          <div className="grid max-h-[480px] grid-cols-3 gap-2 overflow-y-auto sm:grid-cols-4">
            {filtered.map((asset) => (
              <AssetCard
                key={asset.id}
                asset={asset}
                selected={asset.id === selectedId}
                onPick={() => onPick(asset)}
              />
            ))}
          </div>
        )}
      </div>
    </Modal>
  )
}

function AssetCard({
  asset,
  selected,
  onPick,
}: {
  asset: Asset
  selected: boolean
  onPick: () => void
}) {
  const isImg = isImageMime(asset.file_type)
  return (
    <button
      type="button"
      onClick={onPick}
      title={asset.name}
      className={cn(
        'group relative flex aspect-square flex-col overflow-hidden rounded-[8px] border text-left transition-all',
        selected
          ? 'border-accent ring-2 ring-accent/40'
          : 'border-border-faint hover:border-text-mute hover:shadow-sm',
      )}
    >
      {isImg ? (
        <img
          src={asset.preview_url}
          alt={asset.name}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-surface-2 text-text-faint">
          <FileText className="h-8 w-8" />
        </div>
      )}
      <div className="absolute inset-x-0 bottom-0 truncate bg-black/60 px-1.5 py-1 text-[10.5px] text-white">
        {asset.name}
      </div>
    </button>
  )
}

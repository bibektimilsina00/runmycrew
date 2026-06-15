import { useEffect, useMemo, useRef, useState } from 'react'
import { Image as ImageIcon, Link2, Loader2, Upload, X, Search } from 'lucide-react'
import { z } from 'zod'
import { cn } from '@/lib/cn'
import { Input } from '@/shared/components'
import { requestJson } from '@/shared/utils/apiClient'
import apiClient from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import type { RendererProps } from '../types'

/**
 * Field renderer for `type: "media"` properties.
 *
 * Saves a discriminated union into node props so the backend can tell URL
 * input apart from a referenced Asset:
 *
 *   { type: "url",   value: "https://..." }
 *   { type: "asset", asset_id: "<uuid>", name: "...", mime: "image/jpeg" }
 *
 * Bare strings are accepted as input (legacy graphs / `=expression` paths)
 * and rewritten into the `url` shape on first edit so the stored format
 * stays consistent.
 *
 * UI is a 3-tab segmented control: URL ↔ Upload ↔ Library. The Upload tab
 * POSTs to /assets/upload + flips the saved value to the new asset id. The
 * Library tab opens a grid picker over /assets/.
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

type Tab = 'url' | 'upload' | 'library'

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

export function MediaRenderer({
  prop,
  value,
  onChange,
  onPropertiesChange,
  disabled,
}: RendererProps) {
  const opts = (prop.typeOptions ?? {}) as Record<string, unknown>
  const accept = typeof opts.accept === 'string' ? opts.accept : 'image/*,video/*'
  // Name of a sibling property whose value should be auto-set from the
  // picked file's mime. Backwards-compatible: if the node definition
  // doesn't set this, the renderer behaves exactly like before.
  const mediaKindField = typeof opts.mediaKindField === 'string' ? opts.mediaKindField : null

  const current = useMemo(() => normalize(value), [value])
  const [tab, setTab] = useState<Tab>(current.type === 'asset' ? 'library' : 'url')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement | null>(null)

  // Tab state seeds itself from `current.type` on first render and is
  // then user-driven. We deliberately don't re-sync on prop changes:
  // re-rendering with `setTab` inside an effect would cascade renders
  // (and tripped react-hooks/set-state-in-effect), while the initial
  // seed already covers the common open-existing-graph case.

  /** Map a MIME type into the IG content-publishing `kind` enum the
   *  backend node expects. Returns `null` when we shouldn't override
   *  (unknown / generic mime, or no auto-kind wiring configured). */
  const kindFromMime = (mime: string | undefined): string | null => {
    if (!mediaKindField || !mime) return null
    if (mime.startsWith('image/')) return 'IMAGE'
    if (mime === 'video/quicktime') return 'VIDEO' // .mov
    if (mime.startsWith('video/')) return 'VIDEO'
    return null
  }

  const writeWithKind = (next: MediaValue, mime: string | undefined) => {
    const inferred = kindFromMime(mime)
    if (inferred && onPropertiesChange) {
      onPropertiesChange({ [prop.name]: next, [mediaKindField!]: inferred })
    } else {
      onChange(next)
    }
  }

  const setUrl = (v: string) => onChange({ type: 'url', value: v })

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
      writeWithKind(
        {
          type: 'asset',
          asset_id: parsed.id,
          name: parsed.name,
          mime: parsed.file_type,
        },
        parsed.file_type,
      )
      setTab('library')
    } catch (e) {
      const err = e as { detail?: string; message?: string }
      setUploadError(err.detail || err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="inline-flex w-fit rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] p-0.5 text-[11.5px]">
        <TabBtn icon={<Link2 className="h-3 w-3" />} label="URL" active={tab === 'url'} onClick={() => setTab('url')} />
        <TabBtn icon={<Upload className="h-3 w-3" />} label="Upload" active={tab === 'upload'} onClick={() => setTab('upload')} />
        <TabBtn icon={<ImageIcon className="h-3 w-3" />} label="Library" active={tab === 'library'} onClick={() => setTab('library')} />
      </div>

      {tab === 'url' && (
        <Input
          value={current.type === 'url' ? current.value : ''}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={prop.placeholder || 'https://example.com/image.jpg'}
          disabled={disabled}
        />
      )}

      {tab === 'upload' && (
        <div
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            e.stopPropagation()
          }}
          onDrop={(e) => {
            e.preventDefault()
            e.stopPropagation()
            const f = e.dataTransfer.files?.[0]
            if (f) void handleUpload(f)
          }}
          className={cn(
            'flex cursor-pointer flex-col items-center justify-center gap-1 rounded-[8px] border border-dashed border-[var(--border-faint)] bg-[var(--surface)] px-3 py-6 text-center text-[11.5px] text-[var(--text-mute)] hover:bg-[var(--surface-2)]',
            disabled && 'pointer-events-none opacity-50',
          )}
        >
          {uploading ? (
            <Loader2 className="h-4 w-4 animate-spin text-[var(--accent,#3b82f6)]" />
          ) : (
            <Upload className="h-4 w-4 text-[var(--text-faint)]" />
          )}
          <span>{uploading ? 'Uploading…' : 'Drop a file here, or click to browse'}</span>
          <span className="text-[10.5px] text-[var(--text-faint)]">Accepts: {accept}</span>
          {uploadError && <span className="text-[10.5px] text-[var(--err)]">{uploadError}</span>}
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
        </div>
      )}

      {tab === 'library' && (
        <LibraryPicker
          selectedId={current.type === 'asset' ? current.asset_id : null}
          accept={accept}
          onPick={(asset) =>
            writeWithKind(
              {
                type: 'asset',
                asset_id: asset.id,
                name: asset.name,
                mime: asset.file_type,
              },
              asset.file_type,
            )
          }
          disabled={disabled}
        />
      )}

      {current.type === 'asset' && (
        <div className="flex items-center gap-2 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-2 py-1.5 text-[11.5px] text-[var(--text)]">
          <ImageIcon className="h-3.5 w-3.5 text-[var(--accent,#3b82f6)]" />
          <span className="flex-1 truncate" title={current.name}>
            {current.name || current.asset_id}
          </span>
          <span className="font-mono text-[10.5px] text-[var(--text-faint)]">{current.mime}</span>
          <button
            type="button"
            onClick={() => onChange({ type: 'url', value: '' })}
            className="rounded-[4px] p-1 text-[var(--text-faint)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
            title="Clear selection"
            disabled={disabled}
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      )}
    </div>
  )
}

function TabBtn({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex items-center gap-1 rounded-[6px] px-2 py-1 transition-colors',
        active ? 'bg-[var(--surface-2)] text-[var(--text)]' : 'text-[var(--text-mute)] hover:text-[var(--text)]',
      )}
    >
      {icon}
      <span>{label}</span>
    </button>
  )
}

type Asset = z.infer<typeof ASSET_OUT_SCHEMA>

function LibraryPicker({
  selectedId,
  accept,
  onPick,
  disabled,
}: {
  selectedId: string | null
  accept: string
  onPick: (asset: Asset) => void
  disabled?: boolean
}) {
  // Seed `loading=true` so the first paint already shows the spinner;
  // avoids the cascading setState in effect ESLint flags.
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

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

  // Filter by mime prefix (accept rule) + query
  const filtered = useMemo(() => {
    const acceptParts = accept
      .split(',')
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean)
    const q = query.trim().toLowerCase()
    return assets.filter((a) => {
      const mime = a.file_type.toLowerCase()
      const okMime = acceptParts.length === 0 || acceptParts.some((p) => {
        if (p.endsWith('/*')) return mime.startsWith(p.slice(0, -1))
        return mime === p
      })
      if (!okMime) return false
      if (!q) return true
      return a.name.toLowerCase().includes(q)
    })
  }, [assets, accept, query])

  return (
    <div className="flex flex-col gap-2">
      <div className="relative">
        <Search className="absolute left-2 top-1/2 h-3 w-3 -translate-y-1/2 text-[var(--text-faint)]" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search assets…"
          className="pl-7 text-[11.5px]"
          disabled={disabled}
        />
      </div>

      {loading && (
        <div className="flex items-center gap-2 px-1 text-[11.5px] text-[var(--text-faint)]">
          <Loader2 className="h-3 w-3 animate-spin" /> Loading library…
        </div>
      )}
      {error && <div className="px-1 text-[11.5px] text-[var(--err)]">{error}</div>}
      {!loading && !error && filtered.length === 0 && (
        <div className="px-1 text-[11.5px] italic text-[var(--text-faint)]">
          No matching assets in your library yet. Switch to Upload to add one.
        </div>
      )}

      {filtered.length > 0 && (
        <div className="grid max-h-[260px] grid-cols-3 gap-1.5 overflow-y-auto rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] p-1.5">
          {filtered.map((asset) => {
            const isImage = asset.file_type.startsWith('image/')
            const selected = asset.id === selectedId
            return (
              <button
                key={asset.id}
                type="button"
                onClick={() => onPick(asset)}
                className={cn(
                  'group relative flex aspect-square flex-col overflow-hidden rounded-[6px] border text-left text-[10.5px] transition-colors',
                  selected
                    ? 'border-[var(--accent,#3b82f6)] ring-1 ring-[var(--accent,#3b82f6)]'
                    : 'border-[var(--border-faint)] hover:border-[var(--text-mute)]',
                )}
                title={asset.name}
                disabled={disabled}
              >
                {isImage ? (
                  // `preview_url` is the HMAC-signed public route — works
                  // for `<img>` tags without sending the Authorization
                  // header (which `<img>` can't carry).
                  <img
                    src={asset.preview_url}
                    alt={asset.name}
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-[var(--surface-2)] text-[var(--text-faint)]">
                    <ImageIcon className="h-6 w-6" />
                  </div>
                )}
                <div className="absolute bottom-0 left-0 right-0 truncate bg-black/55 px-1 py-0.5 text-[10px] text-white">
                  {asset.name}
                </div>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

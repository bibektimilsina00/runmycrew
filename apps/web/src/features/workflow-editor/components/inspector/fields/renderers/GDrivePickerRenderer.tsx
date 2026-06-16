import { useEffect, useRef, useState } from 'react'
import type { RendererProps } from '../types'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'

/**
 * Google Picker-driven folder selector for Drive trigger / action nodes.
 *
 * `drive.file` is the only non-restricted Drive scope that lets a
 * production app reach Drive at all without going through Google's
 * CASA security assessment. The catch: `drive.file` only exposes
 * files the app itself created OR files the user explicitly granted
 * via the Google Picker. That's why a plain text field for
 * `parent_folder_id` doesn't actually grant Fuse access to the
 * folder — it just stores the id; nothing tells Drive to share it.
 *
 * This renderer fixes the gap: the user clicks a button, Picker opens
 * with the credential's own OAuth token, the user navigates and
 * selects a folder. Picker writes a per-file grant against the OAuth
 * client, and the field stores `{ id, name }` so the runtime cursor
 * can poll the now-visible folder. No CASA, no restricted scope,
 * matches Google's documented production path.
 *
 * The renderer reads the field's *sibling* `credential` property off
 * the inspector graph to fetch a picker token tied to the right
 * Drive account — picking a folder under a different OAuth client
 * would grant access the runtime can't use.
 */

interface PickerValue {
  id: string
  name: string
}

interface PickerTokenResponse {
  access_token: string
  developer_key: string
  app_id: string
}

declare global {
  interface Window {
    gapi?: {
      load: (api: string, cb: () => void) => void
    }
    google?: {
      picker: GooglePickerNamespace
    }
  }
}

interface GooglePickerNamespace {
  ViewId: { FOLDERS: string }
  DocsView: new () => GoogleDocsView
  PickerBuilder: new () => GooglePickerBuilder
  Action: { PICKED: string; CANCEL: string }
  Feature: { SUPPORT_DRIVES: string }
}

interface GoogleDocsView {
  setIncludeFolders(b: boolean): GoogleDocsView
  setSelectFolderEnabled(b: boolean): GoogleDocsView
  setMimeTypes(t: string): GoogleDocsView
}

interface GooglePickerBuilder {
  addView(v: GoogleDocsView): GooglePickerBuilder
  setOAuthToken(t: string): GooglePickerBuilder
  setDeveloperKey(k: string): GooglePickerBuilder
  setAppId(a: string): GooglePickerBuilder
  setOrigin(o: string): GooglePickerBuilder
  enableFeature(f: string): GooglePickerBuilder
  setCallback(cb: (data: PickerCallbackData) => void): GooglePickerBuilder
  setTitle(s: string): GooglePickerBuilder
  build(): { setVisible: (v: boolean) => void }
}

interface PickerCallbackData {
  action: string
  docs?: Array<{ id: string; name: string; mimeType: string }>
}

const PICKER_API_URL = 'https://apis.google.com/js/api.js'

// Tiny cache so the SDK script is requested once per page load even
// when several Drive nodes appear in the same workflow.
let _pickerLoadPromise: Promise<void> | null = null

function loadPicker(): Promise<void> {
  if (window.google?.picker) return Promise.resolve()
  if (_pickerLoadPromise) return _pickerLoadPromise
  _pickerLoadPromise = new Promise((resolve, reject) => {
    // Hard timeout — if the SDK or `gapi.load('picker', ...)` never
    // calls back the button would otherwise spin forever. 15s is well
    // past any reasonable network latency.
    const timer = window.setTimeout(() => {
      reject(
        new Error(
          'Google Picker SDK never loaded — check that the Picker API ' +
            'is enabled on your Google Cloud project and that nothing ' +
            '(ad blocker, CSP) is blocking apis.google.com.',
        ),
      )
    }, 15000)

    const onReady = () => {
      window.clearTimeout(timer)
      resolve()
    }

    const loadPickerModule = () => {
      if (!window.gapi) {
        window.clearTimeout(timer)
        reject(new Error('apis.google.com loaded but `gapi` is undefined'))
        return
      }
      window.gapi.load('picker', () => {
        if (!window.google?.picker) {
          window.clearTimeout(timer)
          reject(
            new Error(
              'gapi.load returned but window.google.picker is missing — ' +
                'the Picker API is probably not enabled on this Google Cloud project.',
            ),
          )
          return
        }
        onReady()
      })
    }

    const existing = document.querySelector(`script[src="${PICKER_API_URL}"]`)
    if (existing) {
      // Script tag already in the DOM. If gapi already loaded we can
      // jump straight to loading the picker module; otherwise wait for
      // the load event the existing tag will fire.
      if (window.gapi) {
        loadPickerModule()
      } else {
        existing.addEventListener('load', loadPickerModule, { once: true })
        existing.addEventListener(
          'error',
          () => {
            window.clearTimeout(timer)
            reject(new Error('Existing apis.google.com script tag errored'))
          },
          { once: true },
        )
      }
      return
    }

    const script = document.createElement('script')
    script.src = PICKER_API_URL
    script.async = true
    script.defer = true
    script.onload = loadPickerModule
    script.onerror = () => {
      window.clearTimeout(timer)
      reject(new Error('Failed to load Google Picker SDK from apis.google.com'))
    }
    document.head.appendChild(script)
  })
  // On failure, clear the cached promise so the next click retries.
  _pickerLoadPromise.catch(() => {
    _pickerLoadPromise = null
  })
  return _pickerLoadPromise
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
  const [opening, setOpening] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const cancelRef = useRef(false)

  useEffect(() => () => {
    cancelRef.current = true
  }, [])

  // The credential the picker needs to authenticate against lives on a
  // sibling property — the inspector hands us the full props bag via
  // `properties` so we can look it up without hard-coding "credential".
  const credentialId =
    typeof properties?.credential === 'string' ? properties.credential : ''

  const openPicker = async () => {
    setError(null)
    if (!credentialId) {
      setError('Pick a Google account on this node first.')
      return
    }
    setOpening(true)
    try {
      const { data } = await apiClient.post<PickerTokenResponse>(
        `/credentials/${credentialId}/picker-token`,
      )
      await loadPicker()
      if (cancelRef.current) return
      const picker = window.google?.picker
      if (!picker) throw new Error('Google Picker SDK not available')

      console.log('[gdrive-picker] SDK ready, building Picker', {
        hasToken: !!data.access_token,
        hasKey: !!data.developer_key,
        appId: data.app_id,
        origin: window.location.origin,
      })

      const docsView = new picker.DocsView()
        .setIncludeFolders(true)
        .setSelectFolderEnabled(true)
        .setMimeTypes('application/vnd.google-apps.folder')

      const builder = new picker.PickerBuilder()
        .addView(docsView)
        .setOAuthToken(data.access_token)
        .setDeveloperKey(data.developer_key)
        .setAppId(data.app_id)
        // Picker iframes are blocked unless we declare the page's origin
        // up-front. Without this, the picker silently refuses to render
        // in some browser / referrer combinations.
        .setOrigin(window.location.protocol + '//' + window.location.host)
        .enableFeature(picker.Feature.SUPPORT_DRIVES)
        .setTitle('Pick a Google Drive folder to watch')
        .setCallback((evt) => {
          console.log('[gdrive-picker] callback', evt.action)
          if (evt.action === picker.Action.PICKED && evt.docs && evt.docs[0]) {
            const doc = evt.docs[0]
            onChange({ id: doc.id, name: doc.name })
          }
        })

      const built = builder.build()
      built.setVisible(true)
      console.log('[gdrive-picker] setVisible(true) called')
    } catch (err) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err as Error)?.message ||
        'Failed to open Google Picker'
      setError(String(msg))
    } finally {
      if (!cancelRef.current) setOpening(false)
    }
  }

  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={openPicker}
          disabled={disabled || opening}
          className={cn(
            'inline-flex items-center gap-1.5 h-8 px-3 rounded-[5px] text-xs font-medium',
            'border border-border bg-surface hover:bg-surface-2 text-text',
            'transition-colors',
            (disabled || opening) && 'opacity-50 cursor-not-allowed',
          )}
        >
          {opening ? 'Opening…' : selected ? 'Change folder' : 'Pick folder'}
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
      {error && (
        <p className="text-[11px] text-[var(--danger,#dc2626)]">{error}</p>
      )}
    </div>
  )
}

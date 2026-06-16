import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Select } from '@/shared/components'
import apiClient from '@/shared/utils/apiClient'
import type { RendererProps } from '../types'

/**
 * Tab (sheet) picker — depends on a sibling `spreadsheet_id` field
 * (which may be a bare string id OR a `{id, name}` dict emitted by
 * the spreadsheet picker). When that sibling has a value, this renderer
 * fetches `/credentials/{cid}/sheets/spreadsheets/{sid}/tabs` and shows
 * a dropdown of tabs.
 *
 * typeOptions.valueAs
 *   - "title"     (default) → emits the tab's title as a string
 *   - "sheet_id"            → emits the numeric sheetId
 *
 * typeOptions.spreadsheetIdField
 *   - sibling property name to read the spreadsheet from. Defaults to
 *     `spreadsheet_id`.
 */

interface TabEntry {
  sheet_id: number
  title: string
  index: number
}

interface TabsResponse {
  tabs: TabEntry[]
}

function readSpreadsheetId(v: unknown): string {
  if (typeof v === 'string') return v
  if (v && typeof v === 'object' && 'id' in v) {
    const obj = v as { id?: unknown }
    return typeof obj.id === 'string' ? obj.id : ''
  }
  return ''
}

export function GSheetsTabPickerRenderer({
  prop,
  value,
  onChange,
  disabled,
  properties,
}: RendererProps) {
  const opts = (prop.typeOptions ?? {}) as Record<string, unknown>
  const valueAs =
    opts.valueAs === 'sheet_id' ? 'sheet_id' : 'title' // default → title
  const spreadsheetIdField =
    typeof opts.spreadsheetIdField === 'string'
      ? opts.spreadsheetIdField
      : 'spreadsheet_id'

  const credentialId =
    typeof properties?.credential === 'string' ? properties.credential : ''
  const spreadsheetId = readSpreadsheetId(properties?.[spreadsheetIdField])

  const [tabs, setTabs] = useState<TabEntry[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Resetting state when the upstream spreadsheet changes is the
    // whole point of this effect — eslint's set-state-in-effect
    // rule doesn't fit data-fetching effects with parent-driven
    // resets.
    if (!credentialId || !spreadsheetId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTabs(null)
      setError(null)
      return
    }
    let alive = true
    setLoading(true)
    setError(null)
    apiClient
      .get<TabsResponse>(
        `/credentials/${credentialId}/sheets/spreadsheets/${spreadsheetId}/tabs`,
      )
      .then(({ data }) => {
        if (!alive) return
        setTabs(data.tabs)
      })
      .catch((err) => {
        if (!alive) return
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          (err as Error)?.message ||
          'Could not load tabs'
        setError(String(msg))
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
  }, [credentialId, spreadsheetId])

  // Convert stored value <-> Select's string value.
  const stringValue = (() => {
    if (value === undefined || value === null || value === '') return ''
    if (valueAs === 'sheet_id') return String(value)
    return String(value)
  })()

  const options =
    tabs?.map((t) => ({
      value: valueAs === 'sheet_id' ? String(t.sheet_id) : t.title,
      label: t.title,
    })) ?? []

  const handleChange = (next: string) => {
    if (valueAs === 'sheet_id') {
      const n = Number(next)
      onChange(Number.isFinite(n) ? n : null)
    } else {
      onChange(next)
    }
  }

  if (!credentialId) {
    return (
      <div className="text-[11.5px] italic text-text-faint">
        Pick a Google account on this node first.
      </div>
    )
  }
  if (!spreadsheetId) {
    return (
      <div className="text-[11.5px] italic text-text-faint">
        Pick a spreadsheet first.
      </div>
    )
  }
  if (loading && !tabs) {
    return (
      <div className="inline-flex items-center gap-1.5 text-[11.5px] text-text-muted">
        <Loader2 className="h-3 w-3 animate-spin" />
        Loading tabs…
      </div>
    )
  }
  if (error) {
    return (
      <div className="text-[11.5px] text-[var(--err,#dc2626)]">{error}</div>
    )
  }
  if (tabs && tabs.length === 0) {
    return (
      <div className="text-[11.5px] italic text-text-faint">
        No tabs found in this spreadsheet.
      </div>
    )
  }

  return (
    <Select
      options={options}
      value={stringValue}
      onChange={handleChange}
      placeholder="Pick a sheet…"
      disabled={disabled}
    />
  )
}

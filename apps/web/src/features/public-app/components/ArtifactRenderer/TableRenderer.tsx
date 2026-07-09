import { useMemo, useState } from 'react'
import { Search } from 'lucide-react'
import type { RendererProps } from './types'

interface Column {
  key: string
  label?: string
  type?: string
}

export function TableRenderer({ artifact }: RendererProps) {
  const columns = (artifact.data?.columns as Column[]) ?? []
  const rows = useMemo(
    () => (artifact.data?.rows as Record<string, unknown>[]) ?? [],
    [artifact.data?.rows],
  )
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return rows
    return rows.filter(r => Object.values(r).some(v => String(v ?? '').toLowerCase().includes(q)))
  }, [rows, query])

  if (columns.length === 0) return <div className="p-6 text-[13px] text-white/50">No columns</div>

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b border-white/5 px-4 py-2">
        <Search size={12} className="text-white/40" />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder={`Filter ${rows.length} row${rows.length === 1 ? '' : 's'}…`}
          className="flex-1 bg-transparent text-[12px] text-white placeholder:text-white/30 focus:outline-none"
        />
      </div>
      <div className="flex-1 overflow-auto">
        <table className="w-full text-[12.5px]">
          <thead className="sticky top-0 bg-black/40 backdrop-blur">
            <tr className="border-b border-white/5">
              {columns.map(c => (
                <th
                  key={c.key}
                  className="whitespace-nowrap px-4 py-2 text-left text-[10.5px] uppercase tracking-wider text-white/50"
                >
                  {c.label || c.key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, i) => (
              <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                {columns.map(c => (
                  <td key={c.key} className="whitespace-nowrap px-4 py-2 text-white/80">
                    {formatCell(row[c.key], c.type)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function formatCell(v: unknown, type?: string): string {
  if (v === null || v === undefined || v === '') return '—'
  if (type === 'number' && typeof v === 'number') return v.toLocaleString()
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

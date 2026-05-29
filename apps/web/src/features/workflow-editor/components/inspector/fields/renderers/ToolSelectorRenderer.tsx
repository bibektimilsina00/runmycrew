import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Input } from '@/shared/components'
import type { NodeProperty } from '../../../../types/editorTypes'

interface Props {
  prop: NodeProperty
  value: unknown
  onChange: (value: unknown) => void
}

type UsageControl = 'auto' | 'force' | 'none'

interface ToolEntry {
  toolId: string
  usageControl: UsageControl
  kind: 'tool' | 'mcp'
}

function toToolArray(value: unknown): ToolEntry[] {
  if (!value) return []
  const arr = typeof value === 'string' ? (() => { try { return JSON.parse(value) } catch { return [] } })() : value
  if (!Array.isArray(arr)) return []
  return arr.filter((i): i is ToolEntry => typeof i === 'object' && i !== null && (i as ToolEntry).kind !== 'mcp')
}

const USAGE_LABELS: Record<UsageControl, string> = { auto: 'Auto', force: 'Force', none: 'Off' }
const USAGE_STYLES: Record<UsageControl, string> = {
  auto: 'bg-surface text-text-mute border-border-faint',
  force: 'bg-ok/10 text-ok border-ok/30',
  none: 'bg-err/10 text-err border-err/30',
}

export function ToolSelectorRenderer({ value, onChange }: Props) {
  const [adding, setAdding] = useState(false)
  const [newId, setNewId] = useState('')
  const tools = toToolArray(value)

  const remove = (i: number) => {
    const next = tools.filter((_, j) => j !== i)
    onChange(next)
  }

  const cycleUsage = (i: number) => {
    const cycle: UsageControl[] = ['auto', 'force', 'none']
    const current = tools[i].usageControl
    const nextUsage = cycle[(cycle.indexOf(current) + 1) % cycle.length]
    onChange(tools.map((t, j) => j === i ? { ...t, usageControl: nextUsage } : t))
  }

  const addTool = () => {
    const id = newId.trim()
    if (!id) return
    const next: ToolEntry[] = [...tools, { toolId: id, usageControl: 'auto', kind: 'tool' }]
    onChange(next)
    setNewId('')
    setAdding(false)
  }

  return (
    <div className="flex flex-col gap-1.5">
      {tools.map((tool, i) => (
        <div key={i} className="flex items-center gap-1.5 rounded-[7px] border border-border-faint bg-bg px-2.5 py-1.5">
          <span className="flex-1 min-w-0 truncate font-mono text-[11px] text-text-mute">{tool.toolId}</span>
          <button
            type="button"
            onClick={() => cycleUsage(i)}
            className={cn(
              'shrink-0 rounded-[4px] border px-1.5 py-0.5 text-[10px] font-medium transition-colors',
              USAGE_STYLES[tool.usageControl],
            )}
          >
            {USAGE_LABELS[tool.usageControl]}
          </button>
          <button
            type="button"
            onClick={() => remove(i)}
            className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-text-faint hover:text-err transition-colors"
          >
            <X size={11} />
          </button>
        </div>
      ))}

      {adding ? (
        <div className="flex items-center gap-1.5">
          <Input
            value={newId}
            onChange={e => setNewId(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') addTool(); if (e.key === 'Escape') { setAdding(false); setNewId('') } }}
            placeholder="tool_id (e.g. slack_send_message)"
            className="h-7 flex-1 font-mono text-[11px]"
            autoFocus
          />
          <button type="button" onClick={addTool} className="h-7 shrink-0 rounded-[6px] bg-accent/10 px-2 text-[11px] text-accent hover:bg-accent/20 transition-colors">Add</button>
          <button type="button" onClick={() => { setAdding(false); setNewId('') }} className="h-7 shrink-0 px-1 text-[11px] text-text-faint hover:text-text-mute">Cancel</button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setAdding(true)}
          className="flex h-7 w-full items-center justify-center gap-1.5 rounded-[7px] border border-dashed border-border-faint text-[11px] text-text-faint hover:border-border-soft hover:text-text-mute transition-colors"
        >
          <Plus size={11} />
          Add tool
        </button>
      )}
    </div>
  )
}

import { useState } from 'react'
import { ChevronDown, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/cn'

interface OutputSchemaSectionProps {
  nodeId: string
  outputs?: { label: string; type: string }[]
}

const typeClass: Record<string, string> = {
  string:  'text-[var(--ok)]',
  number:  'text-[var(--accent)]',
  boolean: 'text-[var(--warn)]',
  object:  'text-[var(--text-mute)]',
  array:   'text-[var(--text-mute)]',
}

export function OutputSchemaSection({ nodeId, outputs = [] }: OutputSchemaSectionProps) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)

  if (outputs.length === 0) return null

  const copyValue = async (label: string) => {
    await navigator.clipboard.writeText(`{{${nodeId}.${label}}}`)
    setCopied(label)
    setTimeout(() => setCopied(null), 1200)
  }

  return (
    <div className="shrink-0 border-t border-[var(--border-faint)]">
      {/* Toggle header */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex h-10 w-full items-center justify-between px-4 transition-colors hover:bg-[var(--surface)]"
      >
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--text-mute)]">
          Outputs
        </span>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] text-[var(--text-dim)]">{outputs.length}</span>
          <ChevronDown
            className={cn('h-3.5 w-3.5 text-[var(--text-faint)] transition-transform duration-200', open && 'rotate-180')}
          />
        </div>
      </button>

      {/* Output rows */}
      {open && (
        <div className="flex flex-col gap-0.5 px-3 pb-3">
          {outputs.map(output => (
            <button
              key={output.label}
              type="button"
              onClick={() => void copyValue(output.label)}
              className="group flex h-8 items-center gap-2 rounded-[7px] px-2 text-left transition-colors hover:bg-[var(--surface)]"
              title={`Copy {{${nodeId}.${output.label}}}`}
            >
              <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-[var(--text)]">
                {output.label}
              </span>
              <span className={cn('font-mono text-[10px]', typeClass[output.type] ?? 'text-[var(--text-faint)]')}>
                {output.type}
              </span>
              {copied === output.label
                ? <Check className="h-3 w-3 text-[var(--ok)]" />
                : <Copy className="h-3 w-3 text-[var(--text-faint)] opacity-0 transition-opacity group-hover:opacity-100" />
              }
            </button>
          ))}
          <p className="mt-0.5 px-2 text-[10px] italic text-[var(--text-dim)]">
            Click to copy interpolation
          </p>
        </div>
      )}
    </div>
  )
}

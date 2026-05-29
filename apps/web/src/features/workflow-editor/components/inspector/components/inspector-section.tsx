import { ChevronDown } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { cn } from '@/lib/cn'

interface InspectorSectionProps {
  title: string
  count?: number
  defaultOpen?: boolean
  children: ReactNode
}

export function InspectorSection({ title, count, defaultOpen = true, children }: InspectorSectionProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <section className="border-b border-[var(--border-faint)]">
      <button
        type="button"
        onClick={() => setOpen(value => !value)}
        className="flex h-9 w-full items-center gap-2 px-4 text-left transition-colors hover:bg-[var(--surface)]"
      >
        <ChevronDown
          className={cn('h-3 w-3 text-[var(--text-faint)] transition-transform', !open && '-rotate-90')}
        />
        <span className="flex-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--text-faint)]">
          {title}
        </span>
        {count !== undefined && (
          <span className="font-mono text-[10px] text-[var(--text-dim)]">{count}</span>
        )}
      </button>
      {open && <div className="flex flex-col gap-4 px-4 pb-4 pt-1">{children}</div>}
    </section>
  )
}

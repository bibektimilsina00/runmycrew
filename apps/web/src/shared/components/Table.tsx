import { type ReactNode, type TdHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

// ── Table root ───────────────────────────────────────────────────────────────

interface TableProps { children: ReactNode; className?: string }

export function Table({ children, className }: TableProps) {
  return (
    <div className={cn('w-full overflow-x-auto rounded-md border border-border-faint', className)}>
      <table className="w-full text-sm border-collapse">{children}</table>
    </div>
  )
}

// ── Head ─────────────────────────────────────────────────────────────────────

export function TableHead({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <thead className={cn('bg-surface border-b border-border-faint', className)}>
      {children}
    </thead>
  )
}

// ── Body ─────────────────────────────────────────────────────────────────────

export function TableBody({ children, className }: { children: ReactNode; className?: string }) {
  return <tbody className={cn('divide-y divide-border-faint', className)}>{children}</tbody>
}

// ── Row ──────────────────────────────────────────────────────────────────────

interface TableRowProps {
  children: ReactNode
  className?: string
  onClick?: () => void
  interactive?: boolean
}

export function TableRow({ children, className, onClick, interactive }: TableRowProps) {
  return (
    <tr
      onClick={onClick}
      className={cn(
        'bg-bg2 transition-colors duration-fast',
        interactive && 'hover:bg-surface cursor-pointer',
        className,
      )}
    >
      {children}
    </tr>
  )
}

// ── Header cell ──────────────────────────────────────────────────────────────

interface TableThProps {
  children: ReactNode
  className?: string
  align?: 'left' | 'center' | 'right'
}

export function TableTh({ children, className, align = 'left' }: TableThProps) {
  return (
    <th
      className={cn(
        'px-4 py-2.5',
        'font-mono text-[10px] tracking-widest uppercase text-text-dim font-medium',
        'whitespace-nowrap',
        align === 'center' && 'text-center',
        align === 'right'  && 'text-right',
        className,
      )}
    >
      {children}
    </th>
  )
}

// ── Data cell ────────────────────────────────────────────────────────────────

interface TableTdProps extends TdHTMLAttributes<HTMLTableCellElement> {
  children: ReactNode
  className?: string
  align?: 'left' | 'center' | 'right'
  muted?: boolean
}

export function TableTd({ children, className, align = 'left', muted, ...props }: TableTdProps) {
  return (
    <td
      {...props}
      className={cn(
        'px-4 py-3 text-sm',
        muted ? 'text-text-faint' : 'text-text',
        align === 'center' && 'text-center',
        align === 'right'  && 'text-right',
        className,
      )}
    >
      {children}
    </td>
  )
}

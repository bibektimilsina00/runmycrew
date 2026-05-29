import { Fragment, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/cn'

export interface ContextMenuItem {
  label: string
  shortcut?: string
  onClick: () => void
  disabled?: boolean
  variant?: 'default' | 'danger'
  dividerBefore?: boolean
}

interface ContextMenuProps {
  x: number
  y: number
  items: ContextMenuItem[]
  onClose: () => void
}

const MENU_W = 200

export function ContextMenu({ x, y, items, onClose }: ContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [onClose])

  const menuH = items.length * 30 + 12
  const left = x + MENU_W > window.innerWidth ? x - MENU_W : x
  const top = y + menuH > window.innerHeight ? Math.max(8, y - menuH) : y

  return createPortal(
    <div
      ref={ref}
      className="fixed z-[9999] w-[200px] rounded-[10px] border border-[var(--border)] bg-[var(--bg-2)] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in zoom-in-95 duration-100"
      style={{ left, top }}
      onContextMenu={e => e.preventDefault()}
    >
      {items.map((item, i) => (
        <Fragment key={i}>
          {item.dividerBefore && <div className="my-[5px] h-px bg-[var(--border-faint)]" />}
          <button
            type="button"
            disabled={item.disabled}
            onClick={() => { if (!item.disabled) { item.onClick(); onClose() } }}
            className={cn(
              'flex w-full items-center justify-between gap-4 rounded-[6px] px-2.5 py-[6px] text-left text-[12.5px] font-medium transition-colors',
              item.disabled && 'cursor-default opacity-35',
              !item.disabled && item.variant === 'danger'
                ? 'text-[var(--err)] hover:bg-[var(--err)]/10'
                : !item.disabled && 'text-[var(--text)] hover:bg-[var(--surface-2)]',
            )}
          >
            <span>{item.label}</span>
            {item.shortcut && (
              <span className="shrink-0 font-mono text-[10.5px] text-[var(--text-faint)]">{item.shortcut}</span>
            )}
          </button>
        </Fragment>
      ))}
    </div>,
    document.body,
  )
}

import { useState, useEffect, useRef, useId, useCallback, type ReactNode, createContext, useContext } from 'react'
import { cn } from '@/lib/cn'

interface DropdownContextValue { open: boolean; setOpen: (v: boolean) => void; triggerId: string; contentId: string }
const DropdownContext = createContext<DropdownContextValue>({ open: false, setOpen: () => {}, triggerId: '', contentId: '' })

interface DropdownProps {
  children: ReactNode
  className?: string
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export function Dropdown({ children, className, open: controlledOpen, onOpenChange }: DropdownProps) {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false)
  const open = controlledOpen !== undefined ? controlledOpen : uncontrolledOpen
  const setOpen = useCallback((v: boolean) => {
    onOpenChange?.(v)
    setUncontrolledOpen(v)
  }, [onOpenChange])
  const ref = useRef<HTMLDivElement>(null)
  const id = useId()
  const triggerId = `dd-trigger-${id}`
  const contentId = `dd-content-${id}`

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', handler)
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('mousedown', handler); document.removeEventListener('keydown', onKey) }
  }, [open, setOpen])

  return (
    <DropdownContext.Provider value={{ open, setOpen, triggerId, contentId }}>
      <div ref={ref} className={cn('relative inline-block', className)} data-state={open ? 'open' : 'closed'}>
        {children}
      </div>
    </DropdownContext.Provider>
  )
}

export function DropdownTrigger({ children, className, disabled }: { children: ReactNode; className?: string; disabled?: boolean }) {
  const { open, setOpen, triggerId, contentId } = useContext(DropdownContext)
  return (
    <div
      id={triggerId}
      aria-haspopup="menu"
      aria-expanded={open}
      aria-controls={contentId}
      className={cn('cursor-pointer', className, disabled && 'pointer-events-none opacity-50')}
      onClick={() => { if (!disabled) setOpen(!open) }}
    >
      {children}
    </div>
  )
}

export function DropdownContent({ children, className }: { children: ReactNode; className?: string }) {
  const { open, contentId, triggerId } = useContext(DropdownContext)
  return (
    <div
      id={contentId}
      role="menu"
      aria-labelledby={triggerId}
      data-state={open ? 'open' : 'closed'}
      className={cn(
        'absolute top-[calc(100%+6px)] left-0 min-w-[200px] z-50 flex flex-col gap-0.5',
        'bg-bg border border-border-faint rounded-[10px] p-1 shadow-dropdown',
        'transition-[opacity,transform] duration-[150ms]',
        open ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 -translate-y-1 pointer-events-none',
        className,
      )}
    >
      {children}
    </div>
  )
}

interface DropdownItemProps {
  children: ReactNode
  onClick?: () => void
  variant?: 'default' | 'danger'
  leftIcon?: ReactNode
  shortcut?: string
  className?: string
  disabled?: boolean
}

export function DropdownItem({ children, onClick, variant = 'default', leftIcon, shortcut, className, disabled }: DropdownItemProps) {
  const { setOpen } = useContext(DropdownContext)
  return (
    <button
      type="button"
      role="menuitem"
      disabled={disabled}
      aria-disabled={disabled}
      onClick={() => { if (!disabled) { onClick?.(); setOpen(false) } }}
      className={cn(
        'flex items-center gap-2 w-full px-3 py-2 rounded-[6px] text-sm text-left',
        'transition-colors duration-[100ms]',
        '[&_svg]:w-3.5 [&_svg]:h-3.5 [&_svg]:shrink-0',
        'disabled:opacity-40 disabled:pointer-events-none',
        variant === 'danger'
          ? 'text-err hover:bg-[var(--badge-err-bg)] [&_svg]:text-err'
          : 'text-text hover:bg-surface [&_svg]:text-text-mute',
        className,
      )}
    >
      {leftIcon && <span className="shrink-0 flex">{leftIcon}</span>}
      <span className="flex-1">{children}</span>
      {shortcut && <span className="text-xs text-text-dim font-mono ml-auto shrink-0">{shortcut}</span>}
    </button>
  )
}

export function DropdownSeparator({ className }: { className?: string }) {
  return <div role="separator" className={cn('h-px bg-border-faint my-1', className)} />
}

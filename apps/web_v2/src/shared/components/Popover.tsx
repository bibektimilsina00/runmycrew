import {
  useState, useEffect, useRef,
  type ReactNode, createContext, useContext,
} from 'react'
import { cn } from '@/lib/cn'

interface PopoverContextValue {
  open: boolean
  setOpen: (v: boolean) => void
}

const PopoverContext = createContext<PopoverContextValue>({ open: false, setOpen: () => {} })

interface PopoverProps { children: ReactNode; className?: string }

export function Popover({ children, className }: PopoverProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <PopoverContext.Provider value={{ open, setOpen }}>
      <div ref={ref} className={cn('relative inline-block', className)}>{children}</div>
    </PopoverContext.Provider>
  )
}

interface PopoverTriggerProps { children: ReactNode; className?: string }

export function PopoverTrigger({ children, className }: PopoverTriggerProps) {
  const { open, setOpen } = useContext(PopoverContext)
  return (
    <div className={cn('cursor-pointer', className)} onClick={() => setOpen(!open)}>
      {children}
    </div>
  )
}

interface PopoverContentProps {
  children: ReactNode
  className?: string
  align?: 'left' | 'right' | 'center'
  width?: string
}

export function PopoverContent({ children, className, align = 'left', width }: PopoverContentProps) {
  const { open } = useContext(PopoverContext)

  const alignCls = {
    left:   'left-0',
    right:  'right-0',
    center: 'left-1/2 -translate-x-1/2',
  }[align]

  return (
    <div
      className={cn(
        'absolute top-[calc(100%+6px)] z-50',
        'bg-bg2 border border-border rounded-md p-4',
        'shadow-dropdown',
        'transition-[opacity,transform] duration-fast',
        alignCls,
        open
          ? 'opacity-100 translate-y-0 pointer-events-auto'
          : 'opacity-0 -translate-y-1 pointer-events-none',
        className,
      )}
      style={width ? { width } : { minWidth: '220px' }}
    >
      {children}
    </div>
  )
}

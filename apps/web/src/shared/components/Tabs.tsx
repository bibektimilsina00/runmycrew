import { useState, useId, type ReactNode, createContext, useContext } from 'react'
import { cn } from '@/lib/cn'

interface TabsContextValue { value: string; onValueChange: (v: string) => void; baseId: string }
const TabsContext = createContext<TabsContextValue>({ value: '', onValueChange: () => {}, baseId: '' })

interface TabsProps { defaultValue?: string; value?: string; onValueChange?: (v: string) => void; children: ReactNode; className?: string }

export function Tabs({ defaultValue = '', value, onValueChange, children, className }: TabsProps) {
  const [internal, setInternal] = useState(defaultValue)
  const baseId = useId()
  const controlled = value !== undefined
  const current = controlled ? value : internal

  return (
    <TabsContext.Provider value={{
      value: current,
      onValueChange: (v) => { if (!controlled) setInternal(v); onValueChange?.(v) },
      baseId,
    }}>
      <div className={cn('flex flex-col', className)}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      role="tablist"
      className={cn('inline-flex items-center border-b border-border-faint gap-0 w-full', className)}
    >
      {children}
    </div>
  )
}

export function TabsTrigger({ value, children, className }: { value: string; children: ReactNode; className?: string }) {
  const { value: current, onValueChange, baseId } = useContext(TabsContext)
  const active = current === value

  return (
    <button
      type="button"
      role="tab"
      id={`${baseId}-tab-${value}`}
      aria-selected={active}
      aria-controls={`${baseId}-panel-${value}`}
      tabIndex={active ? 0 : -1}
      data-state={active ? 'active' : 'inactive'}
      onClick={() => onValueChange(value)}
      className={cn(
        'relative px-4 py-2.5 text-sm font-medium',
        'transition-colors duration-[120ms] cursor-pointer select-none',
        'outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-0',
        active
          ? [
              'text-text',
              'after:absolute after:bottom-0 after:left-0 after:right-0',
              'after:h-[2px] after:bg-text after:rounded-full',
            ].join(' ')
          : 'text-text-faint hover:text-text',
        className,
      )}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, children, className }: { value: string; children: ReactNode; className?: string }) {
  const { value: current, baseId } = useContext(TabsContext)
  return (
    <div
      role="tabpanel"
      id={`${baseId}-panel-${value}`}
      aria-labelledby={`${baseId}-tab-${value}`}
      hidden={current !== value}
      className={cn(current === value && 'animate-fade-in', className)}
    >
      {current === value && children}
    </div>
  )
}

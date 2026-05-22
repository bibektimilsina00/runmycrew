import {
  useState, useEffect, useCallback,
  createContext, useContext, type ReactNode,
} from 'react'
import { X, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react'
import { cn } from '@/lib/cn'

// ── Types ────────────────────────────────────────────────────────────────────

type ToastVariant = 'default' | 'ok' | 'warn' | 'err'

interface ToastItem {
  id: string
  message: string
  description?: string
  variant: ToastVariant
  duration: number
  exiting: boolean
}

interface ToastContextValue {
  toast: (message: string, opts?: Partial<Omit<ToastItem, 'id' | 'exiting'>>) => void
}

// ── Context ──────────────────────────────────────────────────────────────────

const ToastContext = createContext<ToastContextValue>({ toast: () => {} })

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  return useContext(ToastContext)
}

// ── Provider ─────────────────────────────────────────────────────────────────

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.map(t => t.id === id ? { ...t, exiting: true } : t))
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 200)
  }, [])

  const toast = useCallback((message: string, opts?: Partial<Omit<ToastItem, 'id' | 'exiting'>>) => {
    const id = Math.random().toString(36).slice(2)
    const item: ToastItem = {
      id,
      message,
      variant: opts?.variant ?? 'default',
      duration: opts?.duration ?? 4000,
      description: opts?.description,
      exiting: false,
    }
    setToasts(prev => [...prev, item])
    if (item.duration > 0) setTimeout(() => dismiss(id), item.duration)
  }, [dismiss])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <Toaster toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

// ── Icons per variant ────────────────────────────────────────────────────────

const icons: Record<ToastVariant, ReactNode> = {
  default: <Info size={14} />,
  ok:      <CheckCircle size={14} />,
  warn:    <AlertTriangle size={14} />,
  err:     <XCircle size={14} />,
}

const iconColors: Record<ToastVariant, string> = {
  default: 'text-text-mute',
  ok:      'text-ok',
  warn:    'text-warn',
  err:     'text-err',
}

// ── Individual toast ─────────────────────────────────────────────────────────

function ToastItem({ item, onDismiss }: { item: ToastItem; onDismiss: (id: string) => void }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const t = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(t)
  }, [])

  return (
    <div
      className={cn(
        'flex items-start gap-3',
        'bg-bg2 border border-border rounded-md px-3.5 py-3',
        'shadow-dropdown min-w-[280px] max-w-[360px]',
        item.exiting ? 'animate-toast-out' : (visible ? 'animate-toast-in' : 'opacity-0'),
      )}
    >
      <span className={cn('shrink-0 mt-px', iconColors[item.variant])}>
        {icons[item.variant]}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text leading-snug">{item.message}</p>
        {item.description && (
          <p className="text-xs text-text-faint mt-0.5 leading-relaxed">{item.description}</p>
        )}
      </div>
      <button
        onClick={() => onDismiss(item.id)}
        className="shrink-0 text-text-faint hover:text-text-mute transition-colors mt-px"
      >
        <X size={13} />
      </button>
    </div>
  )
}

// ── Toaster portal ───────────────────────────────────────────────────────────

function Toaster({ toasts, onDismiss }: { toasts: ToastItem[]; onDismiss: (id: string) => void }) {
  if (toasts.length === 0) return null
  return (
    <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 items-end">
      {toasts.map(t => (
        <ToastItem key={t.id} item={t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

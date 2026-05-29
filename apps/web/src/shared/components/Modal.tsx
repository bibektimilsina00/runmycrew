import { useEffect, useId, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Button } from './Button'

interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  footer?: ReactNode
  width?: string
  description?: string
}

export function Modal({ open, onClose, title, children, footer, width, description }: ModalProps) {
  const id = useId()
  const titleId = `modal-title-${id}`
  const descId  = `modal-desc-${id}`

  useEffect(() => {
    if (!open) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => { document.body.style.overflow = prev; document.removeEventListener('keydown', onKey) }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-bg/80 backdrop-blur-sm animate-fade-in" aria-hidden="true" />

      {/* Dialog panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? titleId : undefined}
        aria-describedby={description ? descId : undefined}
        data-state="open"
        className={cn(
          'relative bg-bg2 border border-border-faint rounded-[16px]',
          'shadow-modal w-full max-w-md flex flex-col',
          'animate-slide-up',
        )}
        style={width ? { maxWidth: width } : undefined}
        onMouseDown={e => e.stopPropagation()}
      >
        {title && (
          <div className="flex items-center justify-between px-6 py-5 border-b border-border-faint shrink-0">
            <span id={titleId} className="text-base font-semibold tracking-tight text-text">{title}</span>
            <Button variant="icon-sm" onClick={onClose} aria-label="Close dialog"><X size={13} /></Button>
          </div>
        )}

        <div className="px-6 py-5 flex-1 min-h-0">
          {description && <p id={descId} className="sr-only">{description}</p>}
          {children}
        </div>

        {footer && (
          <div className="px-6 py-5 border-t border-border-faint flex items-center justify-end gap-2 shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}

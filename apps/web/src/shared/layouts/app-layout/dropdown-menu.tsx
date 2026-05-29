import { createPortal } from 'react-dom'

interface DropdownMenuProps {
  id: string
  activeId: string | null
  position: { top: number; left: number } | null
  onClose: () => void
  children: React.ReactNode
}

export function DropdownMenu({ id, activeId, position, onClose, children }: DropdownMenuProps) {
  if (activeId !== id || !position) return null

  return createPortal(
    <>
      <div
        style={{ position: 'fixed', inset: 0, zIndex: 9998 }}
        onClick={event => {
          event.stopPropagation()
          onClose()
        }}
      />
      <div
        className="w-[240px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in zoom-in-95 duration-100"
        style={{ position: 'fixed', top: position.top, left: position.left, zIndex: 9999 }}
        onClick={event => event.stopPropagation()}
      >
        {children}
      </div>
    </>,
    document.body
  )
}

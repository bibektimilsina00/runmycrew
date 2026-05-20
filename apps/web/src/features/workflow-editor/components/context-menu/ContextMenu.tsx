import React, { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'

export interface ContextMenuItem {
  label: string
  shortcut?: string
  onClick: () => void
  disabled?: boolean
  active?: boolean   // currently toggled on (shown with bg highlight)
  dividerBefore?: boolean
  variant?: 'default' | 'danger'
}

interface ContextMenuProps {
  x: number
  y: number
  items: ContextMenuItem[]
  onClose: () => void
}

export const ContextMenu: React.FC<ContextMenuProps> = ({ x, y, items, onClose }) => {
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleDown = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) onClose()
    }
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('mousedown', handleDown)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleDown)
      document.removeEventListener('keydown', handleKey)
    }
  }, [onClose])

  // Flip so menu stays on screen
  const menuW = 220
  const menuH = items.length * 30 + 16
  const left = x + menuW > window.innerWidth ? x - menuW : x
  const top = y + menuH > window.innerHeight ? y - menuH : y

  return createPortal(
    <div
      ref={menuRef}
      className="fixed z-[9999] w-[220px] rounded-lg border border-[#2a2a2a] bg-[#1c1c1c] shadow-[0_8px_32px_rgba(0,0,0,0.6)] py-1.5 animate-in fade-in zoom-in-95 duration-100"
      style={{ left, top }}
      onContextMenu={e => e.preventDefault()}
    >
      {items.map((item, i) => (
        <React.Fragment key={i}>
          {item.dividerBefore && <div className="my-1 h-px bg-[#2a2a2a] mx-2" />}
          <button
            disabled={item.disabled}
            onClick={() => { if (!item.disabled) { item.onClick(); onClose() } }}
            className={cn(
              'flex w-full items-center justify-between px-3 py-[5px] text-[13px] font-medium transition-colors text-left mx-0',
              item.disabled && 'opacity-30 cursor-default',
              item.variant === 'danger' && !item.disabled && 'text-white hover:bg-[#3a3a3a]',
              !item.disabled && item.variant !== 'danger' && 'text-white hover:bg-[#2e2e2e]',
              item.active && !item.disabled && '!bg-[#3a3a3a] !text-white',
            )}
          >
            <span>{item.label}</span>
            {item.shortcut && (
              <span className="text-[11px] text-[#666] font-normal ml-4 flex-shrink-0">{item.shortcut}</span>
            )}
          </button>
        </React.Fragment>
      ))}
    </div>,
    document.body
  )
}

// ── Workflow (pane) context menu ──────────────────────────────────────────────

export const PANE_CONTEXT_ITEMS = (params: {
  onUndo: () => void
  onRedo: () => void
  onAddNode: () => void
  onAutoLayout: () => void
  onFitView: () => void
  onOpenLogs: () => void
  onOpenChat: () => void
  canUndo?: boolean
  canRedo?: boolean
}): ContextMenuItem[] => [
  { label: 'Undo', shortcut: '⌘Z', onClick: params.onUndo, disabled: !params.canUndo },
  { label: 'Redo', shortcut: '⌘⇧Z', onClick: params.onRedo, disabled: !params.canRedo },
  { label: 'Add Node', shortcut: '⌘K', onClick: params.onAddNode, dividerBefore: true },
  { label: 'Auto-layout', shortcut: '⇧L', onClick: params.onAutoLayout },
  { label: 'Fit to View', onClick: params.onFitView },
  { label: 'Open Logs', shortcut: '⌘L', onClick: params.onOpenLogs, dividerBefore: true },
  { label: 'Open Chat', onClick: params.onOpenChat },
]

// ── Node (block) context menu ─────────────────────────────────────────────────

export const NODE_CONTEXT_ITEMS = (params: {
  nodeId: string
  isLocked: boolean
  isDisabled?: boolean
  onDuplicate: () => void
  onDisableToggle: () => void
  onFlipHandles: () => void
  onLockToggle: () => void
  onRename: () => void
  onOpenEditor: () => void
  onDelete: () => void
}): ContextMenuItem[] => [
  { label: 'Duplicate', onClick: params.onDuplicate },
  {
    label: params.isDisabled ? 'Enable' : 'Disable',
    onClick: params.onDisableToggle,
    active: params.isDisabled,
    dividerBefore: true,
  },
  { label: 'Flip Handles', onClick: params.onFlipHandles },
  { label: params.isLocked ? 'Unlock' : 'Lock', onClick: params.onLockToggle },
  { label: 'Rename', onClick: params.onRename, dividerBefore: true },
  { label: 'Open Editor', onClick: params.onOpenEditor },
  { label: 'Delete', shortcut: '⌫', onClick: params.onDelete, variant: 'danger', dividerBefore: true },
]

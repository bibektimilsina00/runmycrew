import React, { useRef, useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { MoreHorizontal, LayoutDashboard, Lock, Unlock, Download, Copy, Trash2, History } from 'lucide-react'
import { useParams, useNavigate } from 'react-router-dom'
import { useReactFlow } from 'reactflow'
import { cn } from '@/lib/utils'
import { IconButton } from '@/components/ui'
import { useUpdateWorkflow, useDuplicateWorkflow, useDeleteWorkflow } from '@/features/dashboard/hooks/use-workflows'
import { useWorkflowStore } from '@/stores/workflow-store'
import { VersionHistoryPanel } from '@/features/workflow-editor/controls/VersionHistory'

interface MenuItem {
  label: string
  icon: React.ReactNode
  onClick: () => void
  disabled?: boolean
  variant?: 'danger'
  dividerBefore?: boolean
}

const Menu: React.FC<{ items: MenuItem[]; anchorRect: DOMRect; onClose: () => void }> = ({ items, anchorRect, onClose }) => {
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

  const menuW = 210
  const menuH = items.length * 34 + 12
  const left = anchorRect.right - menuW
  const top = anchorRect.bottom + 4 + menuH > window.innerHeight
    ? anchorRect.top - menuH - 4
    : anchorRect.bottom + 4

  return createPortal(
    <div
      ref={menuRef}
      className="fixed z-[9999] rounded-xl border border-[var(--border-default)] bg-[var(--surface-2)] shadow-[0_8px_32px_rgba(0,0,0,0.5)] py-1.5 animate-in fade-in zoom-in-95 duration-100"
      style={{ left, top, width: menuW }}
      onContextMenu={e => e.preventDefault()}
    >
      {items.map((item, i) => (
        <React.Fragment key={i}>
          {item.dividerBefore && <div className="my-1 h-px bg-[var(--border-default)] mx-2" />}
          <button
            disabled={item.disabled}
            onClick={() => { if (!item.disabled) { item.onClick(); onClose() } }}
            className={cn(
              'flex w-full items-center gap-2.5 px-3 py-[6px] text-[12px] font-medium transition-colors',
              item.disabled && 'opacity-30 cursor-default',
              !item.disabled && item.variant === 'danger' && 'text-red-400 hover:bg-red-500/10',
              !item.disabled && item.variant !== 'danger' && 'text-white hover:bg-[var(--surface-3)]',
            )}
          >
            <span className="flex-shrink-0 opacity-60">{item.icon}</span>
            {item.label}
          </button>
        </React.Fragment>
      ))}
    </div>,
    document.body
  )
}

export const WorkflowOptionsMenu: React.FC = () => {
  const [anchorRect, setAnchorRect] = useState<DOMRect | null>(null)
  const [showVersionHistory, setShowVersionHistory] = useState(false)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const { id: workflowId } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { fitView } = useReactFlow()
  const workflowLocked = useWorkflowStore(s => s.workflowLocked)
  const setWorkflowLocked = useWorkflowStore(s => s.setWorkflowLocked)

  const updateWorkflow = useUpdateWorkflow()
  const duplicateWorkflow = useDuplicateWorkflow()
  const deleteWorkflow = useDeleteWorkflow()

  const handleOpen = () => {
    const rect = buttonRef.current?.getBoundingClientRect()
    if (rect) setAnchorRect(rect)
  }

  const handleExport = () => {
    const { nodes, edges } = useWorkflowStore.getState()
    const data = JSON.stringify({ nodes, edges }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `workflow-${workflowId ?? 'export'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const items: MenuItem[] = [
    {
      label: 'Auto-layout',
      icon: <LayoutDashboard className="w-3.5 h-3.5" />,
      onClick: () => fitView({ duration: 400, padding: 0.2 }),
    },
    {
      label: 'Version history',
      icon: <History className="w-3.5 h-3.5" />,
      onClick: () => setShowVersionHistory(v => !v),
    },
    {
      label: workflowLocked ? 'Unlock workflow' : 'Lock workflow',
      icon: workflowLocked ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />,
      onClick: () => setWorkflowLocked(!workflowLocked),
      dividerBefore: true,
    },
    {
      label: 'Export workflow',
      icon: <Download className="w-3.5 h-3.5" />,
      onClick: handleExport,
    },
    {
      label: 'Duplicate workflow',
      icon: <Copy className="w-3.5 h-3.5" />,
      onClick: () => { if (workflowId) duplicateWorkflow.mutate(workflowId) },
    },
    {
      label: 'Delete workflow',
      icon: <Trash2 className="w-3.5 h-3.5" />,
      onClick: () => {
        if (workflowId && confirm('Delete this workflow? This cannot be undone.')) {
          deleteWorkflow.mutate(workflowId, { onSuccess: () => navigate('/workflows') })
        }
      },
      variant: 'danger',
      dividerBefore: true,
    },
  ]

  return (
    <>
      <IconButton
        ref={buttonRef}
        icon={<MoreHorizontal />}
        tooltip="Workflow options"
        size="sm"
        onClick={handleOpen}
      />
      {anchorRect && (
        <Menu
          items={items}
          anchorRect={anchorRect}
          onClose={() => setAnchorRect(null)}
        />
      )}
      {showVersionHistory && (
        <VersionHistoryPanel onClose={() => setShowVersionHistory(false)} />
      )}
    </>
  )
}

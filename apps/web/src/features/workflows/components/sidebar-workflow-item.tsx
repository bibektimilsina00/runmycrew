import React from 'react'
import { createPortal } from 'react-dom'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Icons } from '@/shared/components/icons'
import { cn } from '@/lib/cn'
import { useNavigate, useLocation } from 'react-router-dom'
import { APP_ROUTES } from '@/shared/constants/routes'
import { type WorkflowWithStats, getWorkflowColor } from '@/features/workflows/types/workflowTypes'

/** Must match NAV_ITEM in app-sidebar.tsx */
const ROW_BASE =
  'flex items-center gap-[10px] py-[6px] px-[10px] rounded-[8px] text-[13px] font-medium w-full cursor-pointer transition-colors duration-100 hover:bg-[var(--surface)] relative'

const MENU_BTN =
  'w-[22px] h-[22px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center opacity-0 transition-all duration-100 shrink-0 hover:bg-[var(--surface-2)] hover:text-[var(--text)] group-hover/wf:opacity-100 [&_svg]:w-[13px] [&_svg]:h-[13px]'

const MENU_ITEM =
  'flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0'

interface SidebarWorkflowItemProps {
  workflow: WorkflowWithStats
  onRename: (id: string, name: string, color: string | null) => void
  onDelete: (id: string, name: string) => void
  onDuplicate: (id: string) => void
  onToggleActive: (id: string, isActive: boolean) => void
  openMenuId: string | null
  setOpenMenuId: (id: string | null) => void
}

export function SidebarWorkflowItem({
  workflow,
  onRename,
  onDelete,
  onDuplicate,
  onToggleActive,
  openMenuId,
  setOpenMenuId,
}: SidebarWorkflowItemProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const isWfActive = location.pathname === APP_ROUTES.WORKFLOW(workflow.id)

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: workflow.id,
    data: { type: 'workflow', workflow },
  })

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.35 : 1,
  }

  const isMenuOpen = openMenuId === workflow.id
  const [menuPos, setMenuPos] = React.useState<{ top: number; left: number } | null>(null)

  const handleMoreClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    if (isMenuOpen) {
      setOpenMenuId(null)
    } else {
      const rect = e.currentTarget.getBoundingClientRect()
      setMenuPos({ top: rect.bottom + 4, left: rect.left })
      setOpenMenuId(workflow.id)
    }
  }

  const closeMenu = () => setOpenMenuId(null)

  const color = getWorkflowColor(workflow)

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="relative group-data-[collapsed=true]/shell:hidden"
    >
      <div
        className={cn(
          ROW_BASE,
          'text-[var(--text-mute)] hover:text-[var(--text)] group/wf',
          isWfActive && "bg-[var(--surface)] text-[var(--text)]",
          isDragging && 'pointer-events-none select-none border border-dashed border-[var(--border)]'
        )}
        title={workflow.name}
        onClick={() => navigate(APP_ROUTES.WORKFLOW(workflow.id))}
      >
        {/* Color dot — fixed 15×15 container so it aligns with icons */}
        <span className="w-[15px] h-[15px] flex items-center justify-center shrink-0">
          <span
            className="w-[7px] h-[7px] rounded-full shrink-0"
            style={{
              backgroundColor: color,
              boxShadow: `0 0 5px ${color}99`,
            }}
          />
        </span>

        <span className="flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis tracking-[-0.005em]">
          {workflow.name}
        </span>

        <button
          className={cn(MENU_BTN, isMenuOpen && 'opacity-100 bg-[var(--surface-2)] text-[var(--text)]')}
          onClick={handleMoreClick}
          onPointerDown={(e) => e.stopPropagation()}
          title="More"
        >
          <Icons.More />
        </button>
      </div>

      {isMenuOpen && menuPos && createPortal(
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 9998 }}
            onClick={(e) => { e.stopPropagation(); closeMenu() }}
            onPointerDown={(e) => e.stopPropagation()}
          />
          <div
            className="w-[240px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in zoom-in-95 duration-100"
            style={{ position: 'fixed', top: menuPos.top, left: menuPos.left, zIndex: 9999 }}
            onClick={(e) => e.stopPropagation()}
            onPointerDown={(e) => e.stopPropagation()}
          >
            <button
              className={MENU_ITEM}
              onClick={(e) => { e.stopPropagation(); closeMenu(); navigate(APP_ROUTES.WORKFLOW(workflow.id)) }}
            >
              <Icons.Edit /> Open in canvas
            </button>
            <button
              className={MENU_ITEM}
              onClick={(e) => { e.stopPropagation(); closeMenu(); navigate(`/runs?workflowId=${workflow.id}`) }}
            >
              <Icons.Activity /> View runs
            </button>
            <button
              className={MENU_ITEM}
              onClick={(e) => { e.stopPropagation(); closeMenu(); onRename(workflow.id, workflow.name, workflow.color || null) }}
            >
              <Icons.Edit /> Rename
            </button>
            <button
              className={MENU_ITEM}
              onClick={(e) => { e.stopPropagation(); closeMenu(); onDuplicate(workflow.id) }}
            >
              <Icons.Copy /> Duplicate
            </button>
            <button
              className={MENU_ITEM}
              onClick={(e) => { e.stopPropagation(); closeMenu(); onToggleActive(workflow.id, !workflow.is_active) }}
            >
              {workflow.is_active ? <Icons.Pause /> : <Icons.Play />}
              {workflow.is_active ? 'Pause workflow' : 'Activate workflow'}
            </button>
            <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
            <button
              className={cn(MENU_ITEM, 'text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.10)]')}
              onClick={(e) => { e.stopPropagation(); closeMenu(); onDelete(workflow.id, workflow.name) }}
            >
              <Icons.Trash /> Delete
            </button>
          </div>
        </>,
        document.body
      )}
    </div>
  )
}

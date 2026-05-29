import { DragOverlay } from '@dnd-kit/core'
import { Icons } from '@/shared/components/icons'
import { type WorkflowWithStats, getWorkflowColor } from '@/features/workflows/types/workflowTypes'

interface WorkflowDragOverlayProps {
  activeWorkflow: WorkflowWithStats | null
}

export function WorkflowDragOverlay({ activeWorkflow }: WorkflowDragOverlayProps) {
  if (!activeWorkflow) return null

  return (
    <DragOverlay dropAnimation={null}>
      <div className="w-[220px] select-none pointer-events-none opacity-90 rotate-2 scale-[1.02] shadow-[0_12px_24px_-10px_oklch(0_0_0/0.8)] border border-[var(--border)] rounded-[8px] bg-[var(--bg-2)]">
        <div className="flex items-center gap-[9px] pt-[6px] pr-[6px] pb-[6px] pl-[12px] rounded-[8px] text-[12.5px] text-[var(--text)] font-medium">
          <span
            className="status-dot"
            style={{
              backgroundColor: getWorkflowColor(activeWorkflow),
              boxShadow: `0 0 6px ${getWorkflowColor(activeWorkflow)}80`,
            }}
          />
          <span className="flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis tracking-tight">
            {activeWorkflow.name}
          </span>
          <button className="w-[22px] h-[22px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center shrink-0">
            <Icons.More />
          </button>
        </div>
      </div>
    </DragOverlay>
  )
}

import React, { useState } from 'react'
import { Hand, ChevronDown, Maximize, MousePointer2, Check, Power } from 'lucide-react'
import { useReactFlow } from 'reactflow'
import { cn } from '@/lib/utils'
import { IconButton, Tooltip } from '@/components/ui'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useUpdateWorkflow } from '@/features/dashboard/hooks/use-workflows'
import { PresenceAvatars } from '../components/PresenceAvatars'

interface WorkflowControlsProps {
  mode: 'select' | 'pan'
  onModeChange: (mode: 'select' | 'pan') => void
}

export const WorkflowControls: React.FC<WorkflowControlsProps> = ({ mode, onModeChange }) => {
  const { fitView } = useReactFlow()
  const [isOpen, setIsOpen] = useState(false)
  const { workflowId, isActive, setIsActive } = useWorkflowStore()
  const updateWorkflow = useUpdateWorkflow()

  const handleToggleActive = async () => {
    if (!workflowId) return
    const next = !isActive
    setIsActive(next)
    updateWorkflow.mutate({ id: workflowId, is_active: next, silent: true })
  }

  return (
    <div className="absolute bottom-4 left-4 z-[100] flex h-[36px] items-center gap-0.5 rounded-lg border border-[var(--border-default)] bg-[var(--surface-1)] p-1 shadow-lg">
      {/* Mode selector */}
      <Tooltip content={mode === 'select' ? 'Select mode' : 'Pan mode'}>
        <div className="relative">
          <div
            className="flex items-center gap-1 px-1 cursor-pointer hover:bg-[var(--surface-hover)] rounded-md transition-colors h-[28px]"
            onClick={() => setIsOpen(!isOpen)}
          >
            <div className="flex items-center justify-center size-[24px] rounded-md bg-[var(--surface-active)] text-white border border-[var(--border-strong)]">
              {mode === 'select'
                ? <MousePointer2 className="size-[12px]" strokeWidth={2.5} />
                : <Hand className="size-[12px]" strokeWidth={2.5} />}
            </div>
            <ChevronDown className={cn('h-[8px] w-[10px] text-[var(--text-muted)] transition-transform', isOpen && 'rotate-180')} />
          </div>

          {isOpen && (
            <div className="absolute bottom-full left-0 mb-2 w-[140px] rounded-lg border border-[var(--border-default)] bg-[var(--surface-2)] p-1 shadow-xl animate-in fade-in slide-in-from-bottom-2">
              {(['select', 'pan'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => { onModeChange(m); setIsOpen(false) }}
                  className={cn(
                    'flex items-center justify-between w-full px-2 py-1.5 rounded-md text-[12px] font-medium transition-all',
                    mode === m ? 'bg-[var(--surface-active)] text-white' : 'text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-white',
                  )}
                >
                  <div className="flex items-center gap-2">
                    {m === 'select' ? <MousePointer2 className="size-[14px]" /> : <Hand className="size-[14px]" />}
                    {m === 'select' ? 'Select' : 'Pan'}
                  </div>
                  {mode === m && <Check className="size-[12px]" />}
                </button>
              ))}
            </div>
          )}
        </div>
      </Tooltip>

      <div className="mx-1 h-[20px] w-[1px] bg-[var(--border-default)]" />

      <IconButton icon={<Maximize className="size-[14px]" strokeWidth={2} />} tooltip="Fit view" size="sm" onClick={() => fitView()} />

      <div className="mx-1 h-[20px] w-[1px] bg-[var(--border-default)]" />

      {/* Presence avatars — other users viewing this workflow */}
      <PresenceAvatars />

      <div className="mx-1 h-[20px] w-[1px] bg-[var(--border-default)]" />

      {/* Active toggle */}
      <Tooltip content={isActive ? 'Workflow active — click to deactivate' : 'Workflow inactive — click to activate'}>
        <button
          onClick={handleToggleActive}
          className={cn(
            'flex items-center gap-1.5 px-2 h-[28px] rounded-md text-[11px] font-medium transition-all',
            isActive
              ? 'text-green-400 hover:bg-green-400/10'
              : 'text-[var(--text-muted)] hover:bg-[var(--surface-hover)] hover:text-white'
          )}
        >
          <Power className={cn('size-[12px]', isActive ? 'text-green-400' : 'text-[var(--text-muted)]')} strokeWidth={2.5} />
          {isActive ? 'Active' : 'Inactive'}
        </button>
      </Tooltip>
    </div>
  )
}

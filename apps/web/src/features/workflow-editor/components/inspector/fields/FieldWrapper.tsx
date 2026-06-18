import { RotateCcw, HelpCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import type { NodeProperty } from '../../../types/editorTypes'
import { Tooltip } from '@/shared/components'

interface FieldWrapperProps {
  prop: NodeProperty
  /** When `canReset` + onReset are both set, renders a small reset chevron. */
  canReset?: boolean
  onReset?: () => void
  children: ReactNode
}

export function FieldWrapper({
  prop,
  canReset,
  onReset,
  children,
}: FieldWrapperProps) {
  const isRequired = prop.required === true

  return (
    <div className="flex flex-col gap-[6px]">
      <div className="flex items-center justify-between gap-2">
        <label className="inline-flex items-center gap-[5px] text-[12px] font-medium text-[var(--text-mute)] leading-none">
          {prop.label}
          {isRequired && (
            <span
              aria-hidden
              className="inline-block w-[4px] h-[4px] rounded-full bg-[var(--err)]"
              title="Required"
            />
          )}
          {prop.description && (
            <Tooltip content={<span className="max-w-[220px] block text-[11px] leading-normal">{prop.description}</span>} delayDuration={150}>
              <HelpCircle className="h-[12.5px] w-[12.5px] text-[var(--text-faint)] hover:text-[var(--text-mute)] cursor-help transition-colors" />
            </Tooltip>
          )}
        </label>
        {canReset && onReset && (
          <button
            type="button"
            onClick={onReset}
            title="Reset to default"
            className="h-[18px] shrink-0 rounded px-1 text-[var(--text-faint)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text-mute)]"
          >
            <RotateCcw className="h-[11px] w-[11px]" />
          </button>
        )}
      </div>

      {children}
    </div>
  )
}

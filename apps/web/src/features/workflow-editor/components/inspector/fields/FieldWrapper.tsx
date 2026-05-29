import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'
import type { NodeProperty } from '../../../types/editorTypes'

interface FieldWrapperProps {
  prop: NodeProperty
  isExpression: boolean
  onToggleExpression: () => void
  children: ReactNode
}

const NO_EXPRESSION_TYPES = new Set(['boolean', 'credential', 'collection', 'fixed-collection', 'tool-selector', 'skill-selector'])

export function FieldWrapper({ prop, isExpression, onToggleExpression, children }: FieldWrapperProps) {
  const supportsExpression = !NO_EXPRESSION_TYPES.has(prop.type)
  const isRequired = prop.required === true

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2">
        <label className="text-[11px] font-semibold uppercase tracking-wide text-text-mute leading-none">
          {prop.label}
          {isRequired && <span className="ml-1 text-err">*</span>}
        </label>
        {supportsExpression && (
          <button
            type="button"
            onClick={onToggleExpression}
            title={isExpression ? 'Switch to manual input' : 'Switch to expression mode'}
            className={cn(
              'h-[18px] shrink-0 rounded px-1.5 font-mono text-[10px] transition-colors',
              isExpression
                ? 'border border-[var(--accent-line)] bg-[var(--accent-line)]/10 text-[var(--accent)]'
                : 'border border-transparent text-text-faint hover:border-border-faint hover:text-text-mute',
            )}
          >
            {'{ }'}
          </button>
        )}
      </div>

      {children}

      {prop.description && (
        <p className="text-[11px] leading-relaxed text-text-faint">{prop.description}</p>
      )}
    </div>
  )
}

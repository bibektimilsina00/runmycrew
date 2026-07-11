import React from 'react'
import { getIcon } from '../../../utils/icon-map'

interface NodeHeaderProps {
  label: string
  icon: string
  color?: string
}

export const NodeHeader = ({ label, icon, color }: NodeHeaderProps) => {
  const isWhite = color === '#ffffff'
  return (
    <div className="flex items-center gap-2 px-2.5 py-1.5 border-b border-border-faint">
      <div
        className={`flex size-[22px] shrink-0 items-center justify-center rounded-[6px] transition-shadow duration-200 ${
          isWhite ? 'bg-white border border-zinc-700/30 shadow-[0_1px_2px_rgba(0,0,0,0.2)]' : 'shadow-sm'
        }`}
        style={!isWhite ? { background: color ?? 'var(--surface-3)' } : undefined}
      >
        {React.cloneElement(getIcon(icon) as React.ReactElement<{ className?: string }>, {
          className: 'size-[15px]',
        })}
      </div>
      <span className="truncate text-[12px] font-semibold text-text leading-none" title={label}>
        {label}
      </span>
    </div>
  )
}

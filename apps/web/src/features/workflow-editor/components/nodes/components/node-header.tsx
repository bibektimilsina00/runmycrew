import React from 'react'
import { getIcon } from '../../../utils/icon-map'

interface NodeHeaderProps {
  label: string
  icon: string
  color?: string
}

export const NodeHeader = ({ label, icon, color }: NodeHeaderProps) => (
  <div className="flex items-center gap-2 px-2.5 py-1.5 border-b border-border-faint">
    <div
      className="flex size-[20px] shrink-0 items-center justify-center rounded-[6px]"
      style={{ background: color ?? 'var(--surface-3)' }}
    >
      {React.cloneElement(getIcon(icon) as React.ReactElement<{ className?: string }>, {
        className: 'size-[12px] text-white',
      })}
    </div>
    <span className="truncate text-[12px] font-semibold text-text leading-none" title={label}>
      {label}
    </span>
  </div>
)

import React from 'react'
import { getIcon } from '../../../utils/icon-map'

interface NodeHeaderProps {
  label: string
  icon: string
  color?: string
}

export const NodeHeader = ({ label, icon, color }: NodeHeaderProps) => (
  <div className="flex items-center gap-2.5 px-3 py-2.5 border-b border-border-faint">
    <div
      className="flex size-[22px] shrink-0 items-center justify-center rounded-[5px]"
      style={{ background: color ?? 'var(--surface-3)' }}
    >
      {React.cloneElement(getIcon(icon) as React.ReactElement, {
        className: 'size-[13px] text-white',
      })}
    </div>
    <span className="truncate text-[13px] font-semibold text-text leading-none" title={label}>
      {label}
    </span>
  </div>
)

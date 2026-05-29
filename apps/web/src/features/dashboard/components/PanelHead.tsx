import React from 'react'

interface PanelHeadProps {
  icon: React.ReactNode
  title: string
  count?: string
  action?: React.ReactNode
}

export function PanelHead({ icon, title, count, action }: PanelHeadProps) {
  return (
    <div className="flex items-center justify-between py-[12px] px-[16px] border-b border-[var(--border-faint)]">
      <div className="flex items-center gap-[8px] text-[13px] font-medium">
        {icon}
        <span>{title}</span>
        {count && <span className="font-mono text-[11px] text-[var(--text-faint)] bg-[var(--surface)] py-[2px] px-[6px] pb-[1px] rounded-[4px] border border-[var(--border-faint)]">{count}</span>}
      </div>
      {action && <div className="flex items-center gap-[4px]">{action}</div>}
    </div>
  )
}

import React from 'react'

interface PanelHeadProps {
  icon: React.ReactNode
  title: string
  count?: string
  countTone?: 'neutral' | 'ok'
  action?: React.ReactNode
}

export function PanelHead({ icon, title, count, countTone = 'neutral', action }: PanelHeadProps) {
  return (
    <div className="flex items-center gap-[9px] pb-[10px] pt-[14px] px-[15px]">
      <span className="inline-flex items-center justify-center text-[var(--text-mute)] [&_svg]:w-[15px] [&_svg]:h-[15px]">
        {icon}
      </span>
      <span className="text-[13.5px] font-semibold text-[var(--text)]">{title}</span>
      {count && (
        <span
          className={
            countTone === 'ok'
              ? 'text-[11px] font-semibold text-[var(--ok)] bg-[var(--badge-ok-bg)] rounded-[5px] py-[2px] px-[7px]'
              : 'text-[11px] font-medium text-[var(--text-mute)] bg-[rgba(255,255,255,0.05)] rounded-[5px] py-[2px] px-[7px] font-mono'
          }
        >
          {count}
        </span>
      )}
      {action && <div className="ml-auto flex items-center gap-[4px]">{action}</div>}
    </div>
  )
}

import React, { memo } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  buildOutputInterpolation,
  writeInterpolationDragData,
} from '@/features/workflow-editor/utils/interpolation'

// --- Shared Types ---
export interface NodeItem {
  id: string
  label: string
  icon: React.ReactNode
  color: string
}

import { Tooltip } from '@/components/ui/tooltip'

// --- Components ---

export const ToolbarButton = memo(({ icon, label, onClick, disabled = false }: { icon: React.ReactNode, label: string, onClick?: () => void, disabled?: boolean }) => (
  <Tooltip content={label} disabled={disabled}>
    <button
      onClick={onClick}
      disabled={disabled}
      className="p-1.5 rounded-md text-[var(--text-muted)] transition-all hover:text-white hover:bg-[var(--surface-hover)] disabled:opacity-20 disabled:cursor-not-allowed"
    >
      {icon}
    </button>
  </Tooltip>
))

export const OptionItem = memo(({ label, checked, onClick }: { label: string, checked: boolean, onClick: () => void }) => (
  <button
    onClick={onClick}
    className="w-full flex items-center justify-between px-2 py-0.5 text-[10px] font-bold text-[var(--text-primary)] hover:bg-[var(--surface-hover)] transition-all"
  >
    <span>{label}</span>
    {checked && <Check className="size-2.5 text-[var(--text-muted)]" strokeWidth={4} />}
  </button>
))

export const LogEntry = memo(({ icon, iconBg, label, duration, active = false, level = 'info', onClick }: { icon: React.ReactNode, iconBg: string, label: string, duration: string, active?: boolean, level?: string, onClick?: () => void }) => (
  <div
    onClick={onClick}
    className={cn(
      "group flex cursor-pointer items-center justify-between gap-2 rounded-lg px-2 h-[30px] transition-all",
      active ? "bg-[var(--surface-active)]" : "hover:bg-[var(--surface-hover)]",
      level === 'error' && !active && "bg-red-500/10 border border-red-500/20"
    )}
  >
    <div className="flex min-w-0 flex-1 items-center gap-2">
      <div 
        className={cn("flex size-[16px] flex-shrink-0 items-center justify-center rounded-sm", level === 'error' && "bg-red-500")} 
        style={{ background: level === 'error' ? undefined : iconBg }}
      >
        {icon}
      </div>
      <span className={cn(
        "min-w-0 truncate text-[13px] font-medium",
        level === 'error' ? "text-red-400" : "text-[var(--text-primary)]"
      )}>
        {label}
      </span>
    </div>
    <span className="flex-shrink-0 text-[12px] text-[var(--text-muted)]">{duration}</span>
  </div>
))

interface DataNodeProps {
  label: string
  value: any
  initialCollapsed?: boolean
  wrap?: boolean
  interpolationNodeId?: string
  interpolationPath?: string[]
}

export const DataNode = memo(({
  label,
  value,
  initialCollapsed = false,
  wrap = false,
  interpolationNodeId,
  interpolationPath,
}: DataNodeProps) => {
  const [isCollapsed, setIsCollapsed] = React.useState(initialCollapsed)
  const isObject = value !== null && typeof value === 'object'
  const displayType = Array.isArray(value) ? 'array' : typeof value
  const canDragInterpolation = Boolean(interpolationNodeId && interpolationPath)
  const interpolation = canDragInterpolation && interpolationNodeId && interpolationPath
    ? buildOutputInterpolation(interpolationNodeId, interpolationPath)
    : null
  
  return (
    <div className="flex min-w-0 overflow-hidden flex-col">
      <div 
        onClick={() => setIsCollapsed(!isCollapsed)} 
        draggable={canDragInterpolation}
        onDragStart={(event) => {
          if (!interpolation) return
          writeInterpolationDragData(event, interpolation)
        }}
        className={cn(
          "group flex min-h-[30px] cursor-pointer items-center gap-2 rounded-lg px-2 -mx-2 hover:bg-[var(--surface-active)] transition-all",
          canDragInterpolation && "cursor-grab active:cursor-grabbing"
        )}
      >
        <span className="text-[12px] font-semibold text-[var(--text-primary)]">{label}</span>
        <div className={cn(
          "inline-flex items-center px-1.5 py-0.5 rounded-sm text-[10px] font-bold tracking-tight", 
          displayType === 'number' ? "bg-blue-500/10 text-blue-400" : 
          displayType === 'boolean' ? "bg-orange-500/10 text-orange-400" :
          (displayType === 'object' || displayType === 'array') ? "bg-purple-500/10 text-purple-400" :
          "bg-text-muted/10 text-text-muted"
        )}>
          {displayType}
        </div>
        <ChevronDown className={cn("size-3 text-[var(--text-muted)] transition-transform duration-200", isCollapsed && "-rotate-90")} />
      </div>
      {!isCollapsed && (
        <div className="mt-1 ml-[4px] border-l border-[var(--border-default)] pl-3 overflow-hidden animate-in fade-in slide-in-from-top-1 duration-200">
          {isObject ? (
            <div className="flex flex-col gap-1">
              {Object.entries(value).map(([k, v]) => (
                <DataNode
                  key={k}
                  label={k}
                  value={v}
                  initialCollapsed={true}
                  wrap={wrap}
                  interpolationNodeId={interpolationNodeId}
                  interpolationPath={interpolationPath ? [...interpolationPath, k] : undefined}
                />
              ))}
              {Object.keys(value).length === 0 && (
                <span className="text-[11px] text-[var(--text-muted)] italic py-1">Empty {displayType}</span>
              )}
            </div>
          ) : (
            <div className={cn("py-0.5 text-[13px] text-[var(--text-body)] font-mono [word-break:break-word]", wrap ? "whitespace-pre-wrap" : "whitespace-pre-wrap overflow-x-auto custom-scrollbar")}>
              {String(value)}
            </div>
          )}
        </div>
      )}
    </div>
  )
})

export const StartIcon = () => (
  <svg width="10" height="10" viewBox="0 0 26 16" fill="none" className="text-white"><path d="M7.8 13C9.23 13 10.45 12.49 11.47 11.47C12.49 10.45 13 9.23 13 7.8C13 6.37 12.49 5.15 11.47 4.13C10.45 3.11 9.23 2.6 7.8 2.6C6.37 2.6 5.15 3.11 4.13 4.13C3.11 5.15 2.6 6.37 2.6 7.8C2.6 9.23 3.11 10.45 4.13 11.47C5.15 12.49 6.37 13 7.8 13ZM7.8 15.6C5.63 15.6 3.79 14.84 2.28 13.33C0.76 11.81 0 9.97 0 7.8C0 5.63 0.76 3.79 2.28 2.28C3.79 0.76 5.63 0 7.8 0C9.75 0 11.45 0.62 12.89 1.85C14.33 3.09 15.2 4.64 15.5 6.5H24.7C25.07 6.5 25.38 6.62 25.63 6.87C25.88 7.12 26 7.43 26 7.8C26 8.17 25.87 8.48 25.63 8.73C25.38 8.98 25.07 9.1 24.7 9.1H15.5C15.2 10.96 14.33 12.51 12.89 13.75C11.44 14.98 9.75 15.6 7.8 15.6Z" fill="currentColor" /></svg>
)

export const ApiIcon = () => (
  <svg width="10" height="10" viewBox="0 0 30 30" fill="none" className="text-white"><path d="M5.61 24.39C8.5 27.28 12.47 25.47 13.56 24.39L15.72 22.22L7.78 14.28L5.61 16.44C4.53 17.53 2.72 21.5 5.61 24.39ZM5.61 24.39L2 28M24.39 5.61C21.5 2.72 17.53 4.53 16.44 5.61L14.28 7.78L22.22 15.72L24.39 13.56C25.47 12.47 27.28 8.5 24.39 5.61ZM24.39 5.61L28 2M15.72 9.22L12.83 12.11M20.78 14.28L17.89 17.17" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
)

export const ToolbarItem = memo(({ label, icon, color, type, onClick }: NodeItem & { type: string, onClick?: () => void }) => {
  const onDragStart = (event: React.DragEvent) => {
    event.dataTransfer.setData('application/reactflow', type)
    event.dataTransfer.effectAllowed = 'move'
    
    // Set custom drag image to ensure transparency and border radius
    const dragImg = event.currentTarget.cloneNode(true) as HTMLElement
    dragImg.style.position = 'absolute'
    dragImg.style.top = '-1000px'
    dragImg.style.width = '220px'
    dragImg.style.opacity = '0.9'
    dragImg.style.borderRadius = '8px'
    dragImg.style.backgroundColor = 'var(--surface-active)'
    document.body.appendChild(dragImg)
    event.dataTransfer.setDragImage(dragImg, 110, 15) // Centered horizontally (220/2) and vertically
    setTimeout(() => document.body.removeChild(dragImg), 0)
  }

  return (
    <div 
      className="flex items-center gap-3 px-4 py-1.5 hover:bg-[var(--surface-hover)] transition-all cursor-grab active:cursor-grabbing group rounded-lg"
      draggable
      onDragStart={onDragStart}
      onClick={onClick}
    >
      <div
        className="flex size-6 items-center justify-center rounded-lg border border-transparent group-hover:border-white/10 shadow-sm"
        style={{ backgroundColor: color }}
      >
        <div className="text-white flex items-center justify-center">
          {React.cloneElement(icon as React.ReactElement, { className: 'size-3' })}
        </div>
      </div>
      <span className="text-[13px] font-medium text-white">{label}</span>
    </div>
  )
})

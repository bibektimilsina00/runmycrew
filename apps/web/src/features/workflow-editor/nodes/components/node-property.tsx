import { Handle, Position } from 'reactflow'
import { cn } from '@/lib/utils'

interface NodePropertyProps {
  label: string
  value: string
  handleId?: string
  handleClass?: string
  labelClass?: string
  direction?: 'vertical' | 'horizontal'
  index?: number
  total?: number
}

export const NodeProperty = ({
  label,
  value,
  handleId,
  handleClass,
  labelClass,
  direction = 'horizontal',
  index = 0,
  total = 1
}: NodePropertyProps) => {
  const isVertical = direction === 'vertical'
  
  const handleBaseClass = "react-flow__handle nodrag nopan !z-[50] !cursor-crosshair !border-none !transition-all !duration-150"
  
  // Horizontal Styles
  const hClass = cn(handleBaseClass, "!h-5 !w-[7px] !bg-[var(--workflow-edge,#555)] !right-[-8px] !rounded-r-[2px] !rounded-l-none hover:!right-[-11px] hover:!rounded-r-full hover:!w-[10px]")
  
  // Vertical Styles
  const vClass = cn(handleBaseClass, "!w-5 !h-[7px] !bg-[var(--workflow-edge,#555)] !bottom-[-8px] !rounded-b-[2px] !rounded-t-none hover:!bottom-[-11px] hover:!rounded-b-full hover:!h-[10px]")

  return (
    <div className="relative flex items-center gap-2 px-3 h-[24px]">
      <span className={cn("min-w-0 truncate text-[var(--text-tertiary)] text-[12px] font-medium capitalize", labelClass)} title={label}>
        {label}
      </span>
      <span className="flex-1 truncate text-right text-[var(--text-primary)] text-[12px]" title={value}>
        {value}
      </span>
      
      {handleId && (
        <Handle
          key={`${handleId}-${direction}`}
          type="source"
          position={isVertical ? Position.Bottom : Position.Right}
          id={handleId}
          className={cn(isVertical ? vClass : hClass, handleClass)}
          style={{ 
            ...(isVertical 
              ? { left: `${((index + 1) * 100) / (total + 1)}%` }
              : { top: '50%' }
            )
          }}
        />
      )}
    </div>
  )
}

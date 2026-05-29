import { Handle, Position } from 'reactflow'
import { cn } from '@/lib/cn'

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

const BASE_HANDLE = 'react-flow__handle nodrag nopan !z-[50] !cursor-crosshair !border-none !transition-all !duration-150 !bg-[var(--border)]'
const H_OUT = cn(BASE_HANDLE, '!h-[18px] !w-[6px] !right-[-7px] !rounded-r-[3px] !rounded-l-none hover:!right-[-10px] hover:!rounded-r-full hover:!w-[9px]')
const V_OUT = cn(BASE_HANDLE, '!w-[18px] !h-[6px] !bottom-[-7px] !rounded-b-[3px] !rounded-t-none hover:!bottom-[-10px] hover:!rounded-b-full hover:!h-[9px]')

export const NodeProperty = ({
  label,
  value,
  handleId,
  handleClass,
  labelClass,
  direction = 'horizontal',
  index = 0,
  total = 1,
}: NodePropertyProps) => {
  const isV = direction === 'vertical'

  const handleStyle: React.CSSProperties = isV
    ? { left: `${((index + 1) * 100) / (total + 1)}%` }
    : { top: '50%' }

  return (
    <div className="relative flex items-center gap-2 px-2.5 h-[18px]">
      <span
        className={cn('min-w-0 truncate text-[11px] font-medium text-text-faint capitalize', labelClass)}
        title={label}
      >
        {label}
      </span>
      <span
        className="flex-1 truncate text-right text-[11px] text-text"
        title={value}
      >
        {value}
      </span>

      {handleId && (
        <Handle
          key={`${handleId}-${direction}`}
          type="source"
          position={isV ? Position.Bottom : Position.Right}
          id={handleId}
          className={cn(isV ? V_OUT : H_OUT, handleClass)}
          style={handleStyle}
        />
      )}
    </div>
  )
}

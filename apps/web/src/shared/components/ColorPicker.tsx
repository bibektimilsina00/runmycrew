import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

export interface ColorPickerProps extends Omit<HTMLAttributes<HTMLDivElement>, 'onChange' | 'value'> {
  value: string | null
  onChange: (value: string | null) => void
  colors?: string[]
}

const DEFAULT_COLORS = [
  '#6366f1', // Indigo
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#f43f5e', // Rose
  '#0ea5e9', // Sky
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#3b82f6', // Blue
]

export const ColorPicker = forwardRef<HTMLDivElement, ColorPickerProps>(
  ({ className, value, onChange, colors = DEFAULT_COLORS, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex items-center gap-[10px] flex-wrap', className)}
        {...props}
      >
        <button
          type="button"
          onClick={() => onChange(null)}
          className={cn(
            "relative w-[28px] h-[28px] rounded-full border border-dashed border-[var(--border)] flex items-center justify-center transition-all duration-100 hover:scale-105 active:scale-95 cursor-pointer",
            value === null ? "ring-2 ring-[var(--text)] ring-offset-2 ring-offset-[var(--bg-2)]" : "opacity-60"
          )}
          title="Random color"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-faint)]" />
        </button>
        {colors.map(c => {
          const isActive = value === c
          return (
            <button
              key={c}
              type="button"
              onClick={() => onChange(c)}
              className={cn(
                "w-[28px] h-[28px] rounded-full transition-all duration-100 hover:scale-105 active:scale-95 flex items-center justify-center cursor-pointer",
                isActive ? "ring-2 ring-[var(--text)] ring-offset-2 ring-offset-[var(--bg-2)]" : "hover:opacity-90"
              )}
              style={{
                backgroundColor: c,
                boxShadow: `0 2px 8px ${c}40`,
              }}
              title={c}
            >
              {isActive && (
                <span className="w-2 h-2 rounded-full bg-white shadow-sm" />
              )}
            </button>
          )
        })}
      </div>
    )
  }
)

ColorPicker.displayName = 'ColorPicker'

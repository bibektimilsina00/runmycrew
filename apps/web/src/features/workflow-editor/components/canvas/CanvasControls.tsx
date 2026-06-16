import React, { useEffect, useRef, useState } from 'react'
import { MiniMap, useViewport } from 'reactflow'
import { ZoomIn, ZoomOut, Maximize2, Brush } from 'lucide-react'
import { cn } from '@/lib/cn'

export interface CanvasControlsProps extends React.HTMLAttributes<HTMLDivElement> {
  onFitView: () => void
  onZoomIn: () => void
  onZoomOut: () => void
  onCleanLayout: () => void
  showMiniMap?: boolean
}

export const CanvasControls = React.forwardRef<HTMLDivElement, CanvasControlsProps>(({
  onFitView,
  onZoomIn,
  onZoomOut,
  onCleanLayout,
  showMiniMap = true,
  className,
  ...props
}, ref) => {
  const { zoom } = useViewport()
  const [isOpen, setIsOpen] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const lastZoomRef = useRef(zoom)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Trigger open when zoom level changes
  useEffect(() => {
    if (zoom !== lastZoomRef.current) {
      lastZoomRef.current = zoom
      setIsOpen(true)

      // Auto-hide after 2.5 seconds if mouse is not hovered over it
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        setIsOpen(false)
      }, 2500)
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [zoom])

  const handleMouseEnter = () => {
    setIsHovered(true)
    if (timerRef.current) clearTimeout(timerRef.current)
  }

  const handleMouseLeave = () => {
    setIsHovered(false)
    if (timerRef.current) clearTimeout(timerRef.current)
    // Hide after 1.5 seconds once mouse leaves
    timerRef.current = setTimeout(() => {
      setIsOpen(false)
    }, 1500)
  }

  return (
    <div
      ref={ref}
      className={cn('absolute bottom-4 left-4 z-10 flex flex-col gap-2.5 pointer-events-none', className)}
      {...props}
    >
      {/* MiniMap showing graph overview — premium themed overlay */}
      {showMiniMap && (
        <div
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          className={cn(
            'pointer-events-auto overflow-hidden rounded-[12px] border border-[var(--border-faint)] bg-[var(--bg-2)]/85 backdrop-blur-md shadow-[0_12px_32px_rgba(0,0,0,0.5)] transition-all duration-300 ease-out origin-bottom-left',
            (isOpen || isHovered)
              ? 'opacity-100 scale-100 translate-y-0 translate-x-0'
              : 'opacity-0 scale-95 translate-y-2 -translate-x-1 pointer-events-none'
          )}
        >
          <MiniMap
            nodeColor="rgba(255, 255, 255, 0.08)"
            maskColor="rgba(0, 0, 0, 0.3)"
            style={{
              position: 'relative',
              background: 'transparent',
              width: 145,
              height: 85,
              margin: 0,
            }}
          />
        </div>
      )}

      {/* Button controls strip */}
      <div className="flex gap-2 pointer-events-auto">
        <button
          onClick={onFitView}
          className={cn(
            'flex h-[34px] w-[34px] items-center justify-center rounded-[8px]',
            'border border-[var(--border-faint)] bg-[var(--bg-2)]/90 backdrop-blur-sm text-[var(--text-mute)] shadow-md',
            'transition-all hover:bg-[var(--surface)] hover:text-[var(--text)] active:scale-95 cursor-pointer'
          )}
          title="Fit view"
        >
          <Maximize2 className="h-4 w-4" />
        </button>
        <button
          onClick={onZoomIn}
          className={cn(
            'flex h-[34px] w-[34px] items-center justify-center rounded-[8px]',
            'border border-[var(--border-faint)] bg-[var(--bg-2)]/90 backdrop-blur-sm text-[var(--text-mute)] shadow-md',
            'transition-all hover:bg-[var(--surface)] hover:text-[var(--text)] active:scale-95 cursor-pointer'
          )}
          title="Zoom in"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={onZoomOut}
          className={cn(
            'flex h-[34px] w-[34px] items-center justify-center rounded-[8px]',
            'border border-[var(--border-faint)] bg-[var(--bg-2)]/90 backdrop-blur-sm text-[var(--text-mute)] shadow-md',
            'transition-all hover:bg-[var(--surface)] hover:text-[var(--text)] active:scale-95 cursor-pointer'
          )}
          title="Zoom out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          onClick={onCleanLayout}
          className={cn(
            'flex h-[34px] w-[34px] items-center justify-center rounded-[8px]',
            'border border-[var(--border-faint)] bg-[var(--bg-2)]/90 backdrop-blur-sm text-[var(--text-mute)] shadow-md',
            'transition-all hover:bg-[var(--surface)] hover:text-[var(--text)] active:scale-95 cursor-pointer'
          )}
          title="Clean canvas view"
        >
          <Brush className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
})

CanvasControls.displayName = 'CanvasControls'

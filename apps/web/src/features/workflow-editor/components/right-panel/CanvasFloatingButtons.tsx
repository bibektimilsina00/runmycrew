import { cn } from '@/lib/cn'
import { Icons } from '@/shared/components'
import { useEditorLayoutStore } from '../../stores/editorLayoutStore'

interface CanvasFloatingButtonsProps {
  onToggleZenMode?: () => void
  zenMode?: boolean
  onAddNodeClick: () => void
  isAddNodeOpen?: boolean
}

/**
 * Floating action buttons that overlay the canvas, anchored to the top-right corner.
 * Matches n8n's style: individual rounded squares floating over the dot-grid canvas.
 */
export function CanvasFloatingButtons({
  onToggleZenMode,
  zenMode = false,
  onAddNodeClick,
  isAddNodeOpen = false,
}: CanvasFloatingButtonsProps) {
  const rightOpen      = useEditorLayoutStore((s) => s.rightOpen)
  const setZoneOpen    = useEditorLayoutStore((s) => s.setZoneOpen)

  const btnBase = cn(
    'w-[38px] h-[38px] rounded-[10px]',
    'bg-[var(--bg-2)] border border-[var(--border-faint)]',
    'flex items-center justify-center',
    'text-[var(--text-mute)] hover:text-[var(--text)] hover:border-[var(--border-soft)]',
    'transition-all duration-150 cursor-pointer shadow-[0_2px_8px_rgba(0,0,0,0.25)]',
  )

  return (
    <div
      className="absolute top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none"
      aria-label="Canvas controls"
    >
      {/* + Add node */}
      <button
        onClick={onAddNodeClick}
        className={cn(
          btnBase,
          'pointer-events-auto',
          isAddNodeOpen && 'bg-[var(--surface)] text-[var(--text)] border-[var(--border-soft)]'
        )}
        title="Add node"
      >
        <Icons.Plus
          className={cn(
            'w-[16px] h-[16px] transition-transform duration-200',
            isAddNodeOpen && 'rotate-45 text-[var(--accent)]'
          )}
        />
      </button>

      {/* Fullscreen / Zen mode toggle */}
      <button
        onClick={onToggleZenMode}
        className={cn(
          btnBase,
          'pointer-events-auto',
          zenMode && 'bg-[var(--surface)] text-[var(--text)] border-[var(--border-soft)]'
        )}
        title={zenMode ? 'Exit fullscreen' : 'Enter fullscreen'}
      >
        <Icons.Maximize className="w-[15px] h-[15px]" />
      </button>

      {/* Documentation */}
      <button
        onClick={() => window.open('https://docs.n8n.io', '_blank')}
        className={cn(btnBase, 'pointer-events-auto')}
        title="Documentation"
      >
        <Icons.Doc className="w-[15px] h-[15px]" />
      </button>

      {/* Toggle right panel (sidebar) */}
      <button
        onClick={() => setZoneOpen('right', !rightOpen)}
        className={cn(
          btnBase,
          'pointer-events-auto',
          rightOpen && 'bg-[var(--surface)] text-[var(--text)] border-[var(--border-soft)]'
        )}
        title={rightOpen ? 'Collapse panel' : 'Expand panel'}
      >
        {rightOpen ? (
          <Icons.PanelClose className="w-[16px] h-[16px]" />
        ) : (
          <Icons.PanelOpen className="w-[16px] h-[16px]" />
        )}
      </button>
    </div>
  )
}

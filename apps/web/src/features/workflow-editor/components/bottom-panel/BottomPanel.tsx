import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { Node as ReactFlowNode } from 'reactflow'
import { cn } from '@/lib/cn'
import { useEditorLayoutStore, type EditorTab } from '../../stores/editorLayoutStore'
import { DRAG_MIME, PANEL_TABS } from '../panels/panel-config'
import { PanelBody } from '../panels/PanelBody'

interface BottomPanelProps {
  nodes: ReactFlowNode[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
  onRun: () => void
  isRunning: boolean
}

const COLLAPSED_HEIGHT = 36

export function BottomPanel({
  nodes,
  updateNodeData,
  onRun,
  isRunning,
}: BottomPanelProps) {
  const panelZones      = useEditorLayoutStore((s) => s.panelZones)
  const bottomActiveTab = useEditorLayoutStore((s) => s.bottomActiveTab)
  const bottomOpen      = useEditorLayoutStore((s) => s.bottomOpen)
  const bottomHeight    = useEditorLayoutStore((s) => s.bottomHeight)
  const setBottomActive = useEditorLayoutStore((s) => s.setBottomActiveTab)
  const setZoneOpen     = useEditorLayoutStore((s) => s.setZoneOpen)
  const toggleZone      = useEditorLayoutStore((s) => s.toggleZone)
  const setBottomHeight = useEditorLayoutStore((s) => s.setBottomHeight)
  const moveTabToZone   = useEditorLayoutStore((s) => s.moveTabToZone)

  const tabs = PANEL_TABS.filter((t) => panelZones[t.id] === 'bottom')
  const [dragOver, setDragOver] = useState(false)
  const [isResizing, setIsResizing] = useState(false)

  // ── Resize ──────────────────────────────────────────────────────────────────
  const dragState = useRef<{ startY: number; startH: number } | null>(null)
  const onResizeMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      dragState.current = { startY: e.clientY, startH: bottomHeight }
      setIsResizing(true)
    },
    [bottomHeight],
  )
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const s = dragState.current
      if (!s) return
      setBottomHeight(s.startH - (e.clientY - s.startY))
    }
    const onUp = () => {
      dragState.current = null
      setIsResizing(false)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
  }, [setBottomHeight])

  // ── Drag-and-drop ───────────────────────────────────────────────────────────
  const onDragOver = (e: React.DragEvent) => {
    if (!Array.from(e.dataTransfer.types).includes(DRAG_MIME)) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (!dragOver) setDragOver(true)
  }
  const onDragLeave = (e: React.DragEvent) => {
    if (e.currentTarget.contains(e.relatedTarget as globalThis.Node | null)) return
    setDragOver(false)
  }
  const onDrop = (e: React.DragEvent) => {
    const tab = e.dataTransfer.getData(DRAG_MIME) as EditorTab
    setDragOver(false)
    if (!tab) return
    moveTabToZone(tab, 'bottom')
  }

  const onTabDragStart = (tab: EditorTab) => (e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData(DRAG_MIME, tab)
    e.dataTransfer.setData('text/plain', tab)
  }

  // collapsed = 36px header, open = bottomHeight.
  const totalHeight = bottomOpen ? bottomHeight : COLLAPSED_HEIGHT

  return (
    <div
      data-role="editor-bottom-panel"
      className={cn(
        'pointer-events-auto relative w-full shrink-0 z-10 flex flex-col overflow-hidden bg-[var(--bg-2)]',
        !isResizing && 'transition-[height] duration-300 ease-in-out',
        dragOver && 'ring-1 ring-inset ring-[var(--accent)]',
        totalHeight > 0 ? 'border-t border-[var(--border-faint)]' : 'border-t-0'
      )}
      style={{ height: totalHeight }}
    >
      {/* Resize handle — only when open */}
      {bottomOpen && (
        <div
          onMouseDown={onResizeMouseDown}
          className="h-1 shrink-0 cursor-row-resize bg-transparent hover:bg-[var(--accent)]/40"
          title="Drag to resize"
        />
      )}

      {/* Tab strip */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className="flex h-[36px] shrink-0 items-stretch border-b border-[var(--border-faint)]"
      >
        <div className="flex flex-1 items-stretch overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {tabs.map(({ id, label, Icon, locked }) => {
            const active = bottomActiveTab === id && bottomOpen
            return (
              <button
                key={id}
                draggable={!locked}
                onDragStart={locked ? undefined : onTabDragStart(id)}
                onClick={() => {
                  if (active) setZoneOpen('bottom', false)
                  else setBottomActive(id)
                }}
                className={cn(
                  'relative flex shrink-0 items-center gap-1.5 px-3 text-[12px] font-medium leading-none whitespace-nowrap transition-colors duration-100',
                  active
                    ? 'text-[var(--text)] [&_svg]:text-[var(--text)]'
                    : 'text-[var(--text-mute)] hover:text-[var(--text)] [&_svg]:text-[var(--text-faint)] hover:[&_svg]:text-[var(--text-mute)]',
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
                {active && (
                  <span className="absolute bottom-[-1px] left-2 right-2 h-[2px] rounded-t-[2px] bg-[var(--text)]" />
                )}
              </button>
            )
          })}
        </div>
        <div className="flex items-center gap-1 px-2">
          <button
            onClick={() => toggleZone('bottom')}
            className="flex h-7 w-7 items-center justify-center rounded-[6px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
            title={bottomOpen ? 'Collapse panel' : 'Expand panel'}
          >
            <ChevronDown
              className={cn(
                'h-3.5 w-3.5 transition-transform duration-160',
                !bottomOpen && 'rotate-180',
              )}
            />
          </button>
        </div>
      </div>

      {/* Body */}
      {bottomOpen && (
        <div className="min-h-0 flex-1 overflow-hidden">
          <PanelBody
            tab={bottomActiveTab}
            nodes={nodes}
            updateNodeData={updateNodeData}
            onRun={onRun}
            isRunning={isRunning}
          />
        </div>
      )}
    </div>
  )
}

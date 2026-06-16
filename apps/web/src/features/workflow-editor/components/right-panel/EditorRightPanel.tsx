import { useState } from 'react'
import type { Node as ReactFlowNode } from 'reactflow'
import { cn } from '@/lib/cn'
import { useEditorLayoutStore, type EditorTab } from '../../stores/editorLayoutStore'
import { DRAG_MIME, PANEL_TABS } from '../panels/panel-config'
import { PanelBody } from '../panels/PanelBody'
import { EditorActionBar } from './EditorActionBar'

interface EditorRightPanelProps {
  nodes: ReactFlowNode[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
  onRun: () => void
  isRunning: boolean
  className?: string
}

const OPEN_WIDTH = 360

export function EditorRightPanel({
  nodes,
  updateNodeData,
  onRun,
  isRunning,
  className,
}: EditorRightPanelProps) {
  const panelZones     = useEditorLayoutStore((s) => s.panelZones)
  const rightActiveTab = useEditorLayoutStore((s) => s.rightActiveTab)
  const rightOpen      = useEditorLayoutStore((s) => s.rightOpen)
  const setRightActive = useEditorLayoutStore((s) => s.setRightActiveTab)
  const moveTabToZone  = useEditorLayoutStore((s) => s.moveTabToZone)

  const tabs = PANEL_TABS.filter((t) => panelZones[t.id] === 'right')
  const [dragOver, setDragOver] = useState(false)

  if (tabs.length === 0) return null

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
    moveTabToZone(tab, 'right')
  }

  const onTabDragStart = (tab: EditorTab) => (e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData(DRAG_MIME, tab)
    e.dataTransfer.setData('text/plain', tab)
  }

  return (
    <aside
      data-role="editor-right-panel"
      className={cn(
        'flex h-full flex-col overflow-hidden border-l border-[var(--border-faint)] bg-[var(--bg-2)] transition-[width] duration-300 ease-in-out shrink-0 select-none',
        dragOver && 'ring-1 ring-inset ring-[var(--accent)]',
        className
      )}
      style={{ width: rightOpen ? OPEN_WIDTH : 0 }}
    >
      {rightOpen && (
        <>
          {/* Action bar */}
          <EditorActionBar onRun={onRun} isRunning={isRunning} />

          {/* Tab strip */}
          <nav
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            className="flex shrink-0 border-b border-[var(--border-faint)] items-stretch overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          >
            {tabs.map(({ id, label, Icon, locked }) => {
              const active = rightActiveTab === id
              return (
                <button
                  key={id}
                  draggable={!locked}
                  onDragStart={locked ? undefined : onTabDragStart(id)}
                  onClick={() => setRightActive(id)}
                  className={cn(
                    'relative flex shrink-0 items-center gap-1.5 px-3 py-2.5 text-[12px] font-medium leading-none whitespace-nowrap transition-colors duration-100',
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
          </nav>

          {/* Panel body */}
          <div className="min-h-0 flex-1 overflow-hidden">
            <PanelBody
              tab={rightActiveTab}
              nodes={nodes}
              updateNodeData={updateNodeData}
              onRun={onRun}
              isRunning={isRunning}
            />
          </div>
        </>
      )}
    </aside>
  )
}

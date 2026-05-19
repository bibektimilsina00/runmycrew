import React, { useState, useRef } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown, ChevronRight, Workflow } from 'lucide-react'
import { useResizable } from '@/features/workflow-editor/hooks/use-resizable'
import { useWorkflowStore } from '@/stores/workflow-store'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import {
  buildOutputInterpolation,
  writeInterpolationDragData,
} from '@/features/workflow-editor/utils/interpolation'

interface ConnectionsPanelProps {
  connectedNodes: { node: any, direction: 'incoming' | 'outgoing' }[]
}

const NodeItem = ({ node, nodeDefinitions }: { node: any, direction: 'incoming' | 'outgoing', nodeDefinitions: any[] }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const def = nodeDefinitions.find(d => d.type === node.type)
  if (!def) return null

  const outputs = def.outputsSchema || []

  return (
    <div className="flex flex-col gap-1 w-full">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "group flex h-[30px] w-full cursor-pointer items-center gap-2 rounded-lg border border-transparent px-2 text-left text-[12px] transition-all outline-none",
          "text-white/90 hover:bg-white/5 hover:text-white"
        )}
      >
        <div 
          className="relative flex size-[16px] flex-shrink-0 items-center justify-center overflow-hidden rounded-sm transition-all"
          style={{ backgroundColor: def.color || '#3b82f6' }}
        >
          <div className="w-[10px] h-[10px] flex items-center justify-center text-white">
            {React.cloneElement(getIcon(def.icon) as React.ReactElement, { size: 10, strokeWidth: 2.5 })}
          </div>
        </div>
        <span className="truncate font-semibold flex-1 mt-[-1px]">{node.data?.label || def.name}</span>
        <ChevronRight className={cn("size-3 text-[var(--text-muted)] transition-transform", isExpanded && "rotate-90")} />
      </button>

      {isExpanded && (
        <div className="ml-[18px] pl-3 border-l border-[var(--border-default)] flex flex-col gap-1.5 py-1 mb-1 animate-in fade-in slide-in-from-left-1 duration-200">
          {outputs.length > 0 ? (
            outputs.map((out) => (
              <div 
                key={out.label} 
                className="flex items-center gap-2 h-5 cursor-grab active:cursor-grabbing hover:bg-white/5 rounded px-1 transition-colors group/item"
                draggable
                onDragStart={(e) => {
                  writeInterpolationDragData(
                    e,
                    buildOutputInterpolation(node.id, [out.label]),
                  )
                }}
              >
                <span className="text-[11px] font-medium text-[var(--text-muted)] group-hover/item:text-white transition-colors">
                  {out.label}
                </span>
                <div className={cn(
                  "inline-flex items-center px-1.5 py-0.5 rounded-sm text-[9px] font-bold tracking-tight opacity-60",
                  out.type === 'number' ? "bg-blue-500/10 text-blue-400" : 
                  out.type === 'boolean' ? "bg-orange-500/10 text-orange-400" :
                  out.type === 'object' ? "bg-purple-500/10 text-purple-400" :
                  "bg-text-muted/10 text-text-muted"
                )}>
                  {out.type}
                </div>
              </div>
            ))
          ) : (
            <span className="text-[11px] text-text-placeholder italic">No output schema defined</span>
          )}
        </div>
      )}
    </div>
  )
}

export const ConnectionsPanel: React.FC<ConnectionsPanelProps> = ({ connectedNodes }) => {
  const [isConnectionsOpen, setIsConnectionsOpen] = useState(true)
  const [panelHeight, setPanelHeight] = useState(220)
  const containerRef = useRef<HTMLDivElement>(null)
  const { nodeDefinitions } = useWorkflowStore()
  
  const heightResizer = useResizable({
    direction: 'vertical',
    minSize: 80,
    maxSize: 600,
    onSizeChange: setPanelHeight,
    containerRef: containerRef as React.RefObject<HTMLElement>,
    invert: true
  })

  return (
    <div 
      ref={containerRef}
      className={cn(
        "flex flex-col border-t border-[var(--border-default)] flex-shrink-0 overflow-hidden bg-[var(--bg)] relative transition-[height] duration-200 ease-in-out",
        !isConnectionsOpen && "select-none"
      )}
      style={{ height: isConnectionsOpen ? panelHeight : 38 }}
    >
      {isConnectionsOpen && (
        <div
          {...heightResizer}
          className="absolute top-0 right-0 left-0 z-50 h-[4px] cursor-ns-resize hover:bg-[var(--brand-accent)] transition-colors"
          role="separator"
        />
      )}
      {/* Panel Header */}
      <div 
        onClick={() => setIsConnectionsOpen(!isConnectionsOpen)}
        className="flex items-center gap-2 h-[38px] px-4 cursor-pointer flex-shrink-0 hover:bg-[var(--surface-active)] transition-colors"
      >
        <ChevronDown className={cn("w-3.5 h-3.5 text-text-muted transition-transform duration-200", !isConnectionsOpen && "-rotate-90")} />
        <h3 className="text-[11px] font-extrabold text-white uppercase tracking-[0.1em]">Connections</h3>
      </div>
      
      {/* Panel Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-2 flex flex-col gap-1">
        {connectedNodes.length > 0 ? (
          connectedNodes.map(item => <NodeItem key={item.node.id} {...item} nodeDefinitions={nodeDefinitions} />)
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center gap-2 opacity-20 py-8">
             <Workflow className="size-8 text-[var(--text-muted)]" />
             <span className="text-[12px] text-text-muted font-medium italic">No connections found</span>
          </div>
        )}
      </div>
    </div>
  )
}

import React, { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import { createPortal } from 'react-dom'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useNodeAncestors } from '@/features/workflow-editor/hooks/use-node-ancestors'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import { ChevronRight, Workflow } from 'lucide-react'


interface InterpolationPickerProps {
  anchorRect: DOMRect | null
  onSelect: (value: string) => void
  onClose: () => void
}

export const InterpolationPicker: React.FC<InterpolationPickerProps> = ({ anchorRect, onSelect, onClose }) => {
  const { nodes, edges, selectedNodeId, nodeDefinitions } = useWorkflowStore()
  const ancestors = useNodeAncestors(selectedNodeId, nodes, edges)
  const [search, setSearch] = useState('')
  const pickerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  if (!anchorRect) return null

  const filteredAncestors = ancestors.filter(a => {
    const def = nodeDefinitions.find(d => d.type === a.node.type)
    const label = a.node.data?.label || def?.name || ''
    return label.toLowerCase().includes(search.toLowerCase())
  })

  return createPortal(
    <div
      ref={pickerRef}
      className="fixed z-[9999] w-[180px] bg-surface-modal border border-white/10 rounded-lg shadow-[0_8px_32px_rgba(0,0,0,0.5)] overflow-hidden animate-in zoom-in-95 duration-150 flex flex-col"
      style={{
        top: anchorRect.bottom + 8,
        left: Math.min(anchorRect.left, window.innerWidth - 190),
        maxHeight: '320px'
      }}
    >
      <div className="p-2 border-b border-white/5">
        <input
          autoFocus
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search variables..."
          className="w-full bg-white/5 border border-white/10 rounded-md px-2 py-1.5 text-[11px] text-white placeholder:text-white/20 focus:outline-none"
        />
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar p-1 flex flex-col gap-0.5">
        {filteredAncestors.length > 0 ? (
          filteredAncestors.map(({ node }) => (
            <PickerNodeItem
              key={node.id}
              node={node}
              onSelect={onSelect}
              def={nodeDefinitions.find(d => d.type === node.type)}
            />
          ))
        ) : (
          <div className="py-3 flex flex-col items-center justify-center opacity-20">
            <Workflow className="size-4 mb-1" />
            <span className="text-[9px]">No connections</span>
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}

const PickerNodeItem = ({ node, onSelect, def }: { node: any, onSelect: (val: string) => void, def: any }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  if (!def) return null

  const outputs = def.outputsSchema || def.outputs_schema || []

  return (
    <div className="flex flex-col gap-0.5">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "flex h-[28px] w-full items-center gap-2 rounded-lg px-2 text-left text-[11px] transition-all outline-none",
          "text-white/80 hover:bg-white/5 hover:text-white"
        )}
      >
        <div
          className="flex size-[14px] flex-shrink-0 items-center justify-center rounded-sm"
          style={{ backgroundColor: def.color || '#3b82f6' }}
        >
          {React.cloneElement(getIcon(def.icon) as React.ReactElement, { size: 9, strokeWidth: 2.5, className: 'text-white' })}
        </div>
        <span className="truncate font-semibold flex-1">{node.data?.label || def.name}</span>
        <ChevronRight className={cn("size-3 text-white/20 transition-transform", isExpanded && "rotate-90")} />
      </button>

      {isExpanded && (
        <div className="ml-[14px] pl-2 border-l border-white/5 flex flex-col gap-0.5 py-0.5 animate-in fade-in slide-in-from-left-1 duration-150">
          {outputs.map((out) => (
            <button
              key={out.label}
              onClick={() => onSelect(`{{${node.id}.output.${out.label}}}`)}
              className="flex items-center justify-between px-2 py-1 rounded-md hover:bg-white/5 text-[10px] group/out"
            >
              <span className="text-white/60 group-hover/out:text-white">{out.label}</span>
              <span className={cn(
                "px-1 rounded-sm text-[8px] font-bold opacity-40 group-hover/out:opacity-80",
                out.type === 'number' ? "bg-blue-500/10 text-blue-400" :
                  out.type === 'boolean' ? "bg-orange-500/10 text-orange-400" :
                    "bg-purple-500/10 text-purple-400"
              )}>
                {out.type}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

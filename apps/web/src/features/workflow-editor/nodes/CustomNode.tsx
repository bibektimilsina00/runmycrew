import { useMemo, useEffect } from 'react'
import { type NodeProps, useUpdateNodeInternals } from 'reactflow'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflow-store'
import { NodeToolbar } from '@/features/workflow-editor/nodes/components/node-toolbar'
import { NodeHeader } from '@/features/workflow-editor/nodes/components/node-header'
import { NodeProperty } from '@/features/workflow-editor/nodes/components/node-property'
import { NodeHandles } from '@/features/workflow-editor/nodes/components/node-handles'
import { getPropValuePreview, shouldShowProperty, getDynamicLabel } from '@/features/workflow-editor/nodes/utils'
import {
  buildCanonicalIndex,
  isSubBlockVisibleForMode,
} from '@/features/workflow-editor/panels/inspector/visibility'
import { useNodeExecutionStatus } from '@/features/workflow-editor/hooks/use-node-execution-status'

export function CustomNode({ id, type, data, selected }: NodeProps) {
  const nodeDefinitions = useWorkflowStore(s => s.nodeDefinitions)
  const definition = useMemo(() => nodeDefinitions.find(d => d.type === type), [type, nodeDefinitions])
  const updateNodeInternals = useUpdateNodeInternals()
  const isLocked = data?.locked ?? false
  const handleDirection = data?.handleDirection ?? 'horizontal'
  const executionStatus = useNodeExecutionStatus(id)

  const canonicalIndex = useMemo(
    () => definition ? buildCanonicalIndex(definition.properties) : { groupsById: {}, canonicalIdByPropName: {} },
    [definition],
  )

  useEffect(() => {
    updateNodeInternals(id)
    const t = setTimeout(() => updateNodeInternals(id), 50)
    return () => clearTimeout(t)
  }, [id, handleDirection, updateNodeInternals])

  if (!definition) return null
  const properties = data.properties || {}
  const canonicalModes = data.canonicalModes || {}

  const visibleProps = definition.properties
    .filter(p => p.visibility !== 'hidden')
    .filter(p => shouldShowProperty(p, properties, definition))
    // Mirror inspector logic: hide standalone advanced fields; respect canonical pair swap
    .filter(p => isSubBlockVisibleForMode(p, false, canonicalIndex, properties, canonicalModes))
  const hasErrorHandle = !!definition.allowError

  return (
    <div className={cn("group relative", executionStatus === 'running' && "node-running-wrapper")}>
      <div
        role="button"
        tabIndex={0}
        className={cn(
          "workflow-drag-handle relative z-[20] w-[200px] select-none rounded-lg border bg-[var(--surface-2)] transition-colors",
          !isLocked ? "cursor-grab [&:active]:cursor-grabbing" : "cursor-default",
          executionStatus === 'completed' && "node-status-completed",
          executionStatus === 'failed'    && "node-status-failed",
          // running: keep normal gray border so the spinning glow wraps around it
          executionStatus === 'running' && "border-border",
          !executionStatus && selected && !isLocked && "border-[#555]",
          !executionStatus && (!selected || isLocked) && "border-border",
        )}
      >
        <NodeToolbar id={id} />
        <NodeHandles definition={definition} direction={handleDirection} />

        <NodeHeader 
          label={data.label || definition.name} 
          icon={definition.icon} 
          color={definition.color} 
        />

        {/* Properties list */}
        <div className="flex flex-col gap-1.5 py-2">
          {visibleProps.map((prop) => {
            const modes = data.properties?._modes || {}
            const mode = modes[prop.name] || (prop.loadOptions ? 'dynamic' : 'manual')
            return (
              <NodeProperty 
                key={prop.name} 
                label={getDynamicLabel(prop, mode)} 
                value={getPropValuePreview(data.properties?.[prop.name], prop.type)} 
              />
            )
          })}
          
          {hasErrorHandle && (
            <NodeProperty
              label="error"
              value=""
              handleId="error"
              handleClass="!bg-red-500"
              labelClass="!text-red-400"
            />
          )}
        </div>
      </div>
    </div>
  )
}


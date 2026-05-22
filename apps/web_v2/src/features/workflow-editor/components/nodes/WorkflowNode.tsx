import { useMemo, useEffect } from 'react'
import { type NodeProps, useUpdateNodeInternals } from 'reactflow'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'
import { NodeToolbar } from './components/node-toolbar'
import { NodeHeader } from './components/node-header'
import { NodeProperty } from './components/node-property'
import { NodeHandles } from './components/node-handles'
import { getPropValuePreview, getDynamicLabel, shouldShowProperty } from '../../utils/nodeUtils'
import { useNodeExecutionStatus } from '../../hooks/useNodeExecutionStatus'

export function WorkflowNode({ id, type, data, selected }: NodeProps) {
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)
  const definition = useMemo(() => nodeDefinitions.find(d => d.type === type), [type, nodeDefinitions])
  const updateNodeInternals = useUpdateNodeInternals()
  const isLocked = data?.locked ?? false
  const handleDirection: 'horizontal' | 'vertical' = data?.handleDirection ?? 'horizontal'
  const executionStatus = useNodeExecutionStatus(id)

  useEffect(() => {
    updateNodeInternals(id)
    const t = setTimeout(() => updateNodeInternals(id), 50)
    return () => clearTimeout(t)
  }, [id, handleDirection, updateNodeInternals])

  if (!definition) return null

  const properties: Record<string, unknown> = data.properties ?? {}

  const visibleProps = definition.properties
    .filter(p => p.visibility !== 'hidden')
    .filter(p => shouldShowProperty(p, properties))

  const hasErrorHandle = !!definition.allowError

  return (
    <div className={cn('group relative', executionStatus === 'running' && 'node-running-wrapper')}>
      <div
        role="button"
        tabIndex={0}
        className={cn(
          'workflow-drag-handle relative z-[20] w-[200px] select-none rounded-[10px] border bg-bg2 transition-colors',
          !isLocked ? 'cursor-grab active:cursor-grabbing' : 'cursor-default',
          executionStatus === 'completed' && 'node-status-completed',
          executionStatus === 'failed'    && 'node-status-failed',
          executionStatus === 'running'   && 'border-border',
          !executionStatus && selected && !isLocked && 'border-accent-line',
          !executionStatus && (!selected || isLocked) && 'border-border',
        )}
      >
        <NodeToolbar id={id} />
        <NodeHandles definition={definition} direction={handleDirection} />

        <NodeHeader
          label={data.label as string || definition.name}
          icon={definition.icon}
          color={definition.color}
        />

        <div className="flex flex-col gap-0.5 py-2">
          {visibleProps.map(prop => {
            const modes = (data.properties as Record<string, unknown>)?._modes as Record<string, string> | undefined
            const mode = modes?.[prop.name] ?? (prop.loadOptions ? 'dynamic' : 'manual')
            return (
              <NodeProperty
                key={prop.name}
                label={getDynamicLabel(prop, mode as 'manual' | 'dynamic')}
                value={getPropValuePreview(properties[prop.name], prop.type)}
              />
            )
          })}

          {hasErrorHandle && (
            <NodeProperty
              label="error"
              value=""
              handleId="error"
              handleClass="!bg-err"
              labelClass="!text-err"
            />
          )}
        </div>
      </div>
    </div>
  )
}

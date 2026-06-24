import { useMemo, useEffect } from 'react'
import { type NodeProps, useUpdateNodeInternals } from 'reactflow'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../../stores/editorLayoutStore'
import { NodeToolbar } from './components/node-toolbar'
import { NodeHeader } from './components/node-header'
import { NodeProperty } from './components/node-property'
import { NodeHandles } from './components/node-handles'
import { getPropValuePreview, getDynamicLabel, getVisibleNodeProperties } from '../../utils/nodeUtils'
import { useNodeExecutionStatus } from '../../hooks/useNodeExecutionStatus'

export function WorkflowNode({ id, type, data, selected }: NodeProps) {
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)
  const definition = useMemo(() => nodeDefinitions.find(d => d.type === type), [type, nodeDefinitions])
  const nodeUI = useEditorLayoutStore(s => s.nodeUI[id])
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
  const showAdvanced = nodeUI?.showAdvanced ?? false
  const diffMark = data?.__diff as 'new' | 'edited' | 'deleted' | undefined

  const visibleProps = getVisibleNodeProperties(definition.properties, properties, showAdvanced)

  const hasErrorHandle = !!definition.allowError

  return (
    <div className={cn('group relative', executionStatus === 'running' && 'node-running-wrapper')}>
      <div
        role="button"
        tabIndex={0}
        className={cn(
          'workflow-drag-handle relative z-[20] w-[210px] select-none rounded-[8px] border bg-bg2 transition-colors',
          !isLocked ? 'cursor-grab active:cursor-grabbing' : 'cursor-default',
          // Copilot diff overlay takes precedence over normal state styling
          diffMark === 'new'     && 'border-[var(--ok)] shadow-[0_0_0_1px_var(--ok)]',
          diffMark === 'edited'  && 'border-[var(--warn)] shadow-[0_0_0_1px_var(--warn)]',
          diffMark === 'deleted' && 'border-dashed border-[var(--err)] opacity-50',
          !diffMark && executionStatus === 'completed' && 'node-status-completed',
          !diffMark && executionStatus === 'failed'    && 'node-status-failed',
          !diffMark && executionStatus === 'running'   && 'border-border',
          !diffMark && !executionStatus && selected && !isLocked && 'border-[var(--text-dim)] shadow-[0_0_0_1px_var(--text-dim)]',
          !diffMark && !executionStatus && (!selected || isLocked) && 'border-border',
        )}
      >
        <NodeToolbar id={id} selected={!!selected} />
        <NodeHandles definition={definition} direction={handleDirection} />

        <NodeHeader
          label={data.label as string || definition.name}
          icon={definition.icon}
          color={definition.color}
        />

        <div className="flex flex-col gap-0.5 py-1.5">
          {visibleProps.map(prop => (
            <NodeProperty
              key={prop.name}
              label={getDynamicLabel(prop)}
              value={getPropValuePreview(properties[prop.name], prop.type)}
            />
          ))}

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

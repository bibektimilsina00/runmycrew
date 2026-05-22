import type { ComponentType } from 'react'
import type { NodeProps } from 'reactflow'
import type { NodeDefinition } from '../types/editorTypes'
import { WorkflowNode } from '../components/nodes/WorkflowNode'

// Add custom renderers here when a node type needs special canvas UI.
// Every type not listed falls back to WorkflowNode.
export const CUSTOM_RENDERERS: Record<string, ComponentType<NodeProps>> = {
  // condition: ConditionNode,
  // loop: LoopNode,
}

export function buildNodeTypes(
  definitions: NodeDefinition[],
): Record<string, ComponentType<NodeProps>> {
  return Object.fromEntries(
    definitions.map(d => [d.type, CUSTOM_RENDERERS[d.type] ?? WorkflowNode]),
  )
}

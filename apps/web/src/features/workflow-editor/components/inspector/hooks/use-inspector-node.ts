import { useMemo, useCallback } from 'react'
import type { Node } from 'reactflow'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'
import type { NodeDefinition } from '../../../types/editorTypes'
import { getDefaultPropertyValue, splitPropertyGroups } from '../utils/inspector-visibility'

interface UseInspectorNodeParams {
  nodes: Node[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
}

export function useInspectorNode({ nodes, updateNodeData }: UseInspectorNodeParams) {
  const selectedNodeId = useWorkflowEditorStore(s => s.selectedNodeId)
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)
  const setSelectedNodeId = useWorkflowEditorStore(s => s.setSelectedNodeId)
  const setInspectorOpen = useWorkflowEditorStore(s => s.setInspectorOpen)

  const selectedNode = useMemo(
    () => nodes.find(node => node.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId],
  )

  const definition = useMemo<NodeDefinition | null>(
    () => selectedNode ? nodeDefinitions.find(item => item.type === selectedNode.type) ?? null : null,
    [nodeDefinitions, selectedNode],
  )

  const properties = useMemo<Record<string, unknown>>(
    () => selectedNode?.data?.properties ?? {},
    [selectedNode],
  )

  const groups = useMemo(
    () => definition ? splitPropertyGroups(definition.properties, properties) : { basicGroups: [], advancedGroups: [] },
    [definition, properties],
  )

  const updateProperty = useCallback((name: string, value: unknown) => {
    if (!selectedNode) return

    // Handle expression mode toggle from PropertyField
    if (typeof value === 'object' && value !== null && (value as { __modes_update?: boolean }).__modes_update) {
      const { modes } = value as { modes: Record<string, string> }
      updateNodeData(selectedNode.id, {
        properties: {
          ...(selectedNode.data?.properties ?? {}),
          _modes: modes,
        },
      })
      return
    }

    updateNodeData(selectedNode.id, {
      properties: {
        ...(selectedNode.data?.properties ?? {}),
        [name]: value,
      },
    })
  }, [selectedNode, updateNodeData])

  const updateLabel = useCallback((label: string) => {
    if (!selectedNode) return
    updateNodeData(selectedNode.id, { label })
  }, [selectedNode, updateNodeData])

  const ensureDefault = useCallback((name: string) => {
    if (!definition || !selectedNode) return
    const prop = definition.properties.find(item => item.name === name)
    if (!prop || properties[name] !== undefined) return
    updateProperty(name, getDefaultPropertyValue(prop))
  }, [definition, properties, selectedNode, updateProperty])

  const closeInspector = useCallback(() => {
    setSelectedNodeId(null)
    setInspectorOpen(false)
  }, [setInspectorOpen, setSelectedNodeId])

  const showAdvanced = (selectedNode?.data?.showAdvanced as boolean | undefined) ?? false

  const toggleAdvanced = useCallback(() => {
    if (!selectedNode) return
    updateNodeData(selectedNode.id, { showAdvanced: !showAdvanced })
  }, [selectedNode, showAdvanced, updateNodeData])

  return {
    selectedNode,
    definition,
    properties,
    basicGroups: groups.basicGroups,
    advancedGroups: groups.advancedGroups,
    showAdvanced,
    toggleAdvanced,
    updateProperty,
    updateLabel,
    ensureDefault,
    closeInspector,
  }
}

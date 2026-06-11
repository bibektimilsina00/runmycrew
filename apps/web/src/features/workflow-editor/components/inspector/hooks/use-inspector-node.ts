import { useMemo, useCallback } from 'react'
import type { Node } from 'reactflow'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../../../stores/editorLayoutStore'
import type { NodeDefinition } from '../../../types/editorTypes'
import { splitPropertyGroups } from '../utils/inspector-visibility'

interface UseInspectorNodeParams {
  nodes: Node[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
}

/**
 * Glue between the workflow store and the inspector UI.
 *
 * UI-only state (advanced-fields toggle, per-field manual/expression mode) is
 * read/written via `editorLayoutStore` so it never lands in the saved graph.
 * Property values live on the node itself as before.
 */
export function useInspectorNode({ nodes, updateNodeData }: UseInspectorNodeParams) {
  const selectedNodeId  = useWorkflowEditorStore(s => s.selectedNodeId)
  const nodeDefinitions = useWorkflowEditorStore(s => s.nodeDefinitions)
  const setSelectedNodeId = useWorkflowEditorStore(s => s.setSelectedNodeId)

  const nodeUI = useEditorLayoutStore(s => (selectedNodeId ? s.nodeUI[selectedNodeId] : undefined))
  const setNodeShowAdvanced = useEditorLayoutStore(s => s.setNodeShowAdvanced)
  const setNodeFieldMode    = useEditorLayoutStore(s => s.setNodeFieldMode)

  const selectedNode = useMemo(
    () => nodes.find(node => node.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId],
  )

  const definition = useMemo<NodeDefinition | null>(
    () => selectedNode ? nodeDefinitions.find(item => item.type === selectedNode.type) ?? null : null,
    [nodeDefinitions, selectedNode],
  )

  const properties = useMemo<Record<string, unknown>>(
    () => (selectedNode?.data?.properties as Record<string, unknown> | undefined) ?? {},
    [selectedNode],
  )

  const groups = useMemo(
    () => definition ? splitPropertyGroups(definition.properties, properties) : { basicGroups: [], advancedGroups: [] },
    [definition, properties],
  )

  const updateProperty = useCallback((name: string, value: unknown) => {
    if (!selectedNode) return
    updateNodeData(selectedNode.id, {
      properties: {
        ...((selectedNode.data?.properties as Record<string, unknown> | undefined) ?? {}),
        [name]: value,
      },
    })
  }, [selectedNode, updateNodeData])

  const updateLabel = useCallback((label: string) => {
    if (!selectedNode) return
    updateNodeData(selectedNode.id, { label })
  }, [selectedNode, updateNodeData])

  const fieldModes = nodeUI?.fieldModes
  const setFieldMode = useCallback((field: string, mode: 'manual' | 'dynamic') => {
    if (!selectedNode) return
    setNodeFieldMode(selectedNode.id, field, mode)
  }, [selectedNode, setNodeFieldMode])

  const showAdvanced = nodeUI?.showAdvanced ?? false
  const toggleAdvanced = useCallback(() => {
    if (!selectedNode) return
    setNodeShowAdvanced(selectedNode.id, !showAdvanced)
  }, [selectedNode, showAdvanced, setNodeShowAdvanced])

  const closeInspector = useCallback(() => {
    setSelectedNodeId(null)
  }, [setSelectedNodeId])

  return {
    selectedNode,
    definition,
    properties,
    basicGroups: groups.basicGroups,
    advancedGroups: groups.advancedGroups,
    showAdvanced,
    toggleAdvanced,
    fieldModes,
    setFieldMode,
    updateProperty,
    updateLabel,
    closeInspector,
  }
}

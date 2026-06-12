import { useMemo, useCallback } from 'react'
import type { Node } from 'reactflow'
import { useWorkflowEditorStore } from '../../../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../../../stores/editorLayoutStore'
import type { NodeDefinition } from '../../../types/editorTypes'
import { splitPropertyGroups } from '../utils/inspector-visibility'
import { renameNodeInGraph, validateNodeLabel } from '../../../utils/rename-refactor'

interface UseInspectorNodeParams {
  nodes: Node[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
}

/**
 * Glue between the workflow store and the inspector UI.
 *
 * Per-node UI prefs (advanced-fields toggle) are read/written via
 * `editorLayoutStore` so they never land in the saved graph. Property values
 * live on the node itself as before.
 */
export function useInspectorNode({ nodes, updateNodeData }: UseInspectorNodeParams) {
  const selectedNodeId    = useWorkflowEditorStore(s => s.selectedNodeId)
  const nodeDefinitions   = useWorkflowEditorStore(s => s.nodeDefinitions)
  const setSelectedNodeId = useWorkflowEditorStore(s => s.setSelectedNodeId)

  const nodeUI = useEditorLayoutStore(s => (selectedNodeId ? s.nodeUI[selectedNodeId] : undefined))
  const setNodeShowAdvanced = useEditorLayoutStore(s => s.setNodeShowAdvanced)

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

  /**
   * Rename the selected node atomically with `$node('Old')` → `$node('New')`
   * rewriting across every other node's properties. Returns the user-facing
   * reason for rejection, or `null` when the rename was applied.
   *
   * The validate+apply step uses `getState().setNodes` rather than the
   * `updateNodeData` prop because the rename touches multiple nodes — not
   * just the selected one — and `updateNodeData` is single-node by design.
   */
  const updateLabel = useCallback((label: string): string | null => {
    if (!selectedNode) return null
    const store = useWorkflowEditorStore.getState()
    const error = validateNodeLabel(selectedNode.id, label, store.nodes)
    if (error) return error
    store.setNodes(renameNodeInGraph(store.nodes, selectedNode.id, label.trim()))
    return null
  }, [selectedNode])

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
    updateProperty,
    updateLabel,
    closeInspector,
  }
}

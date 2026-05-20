import { useCallback, useRef, useState } from 'react';
import type React from 'react';
import { useWorkflowStore } from '@/stores/workflow-store';
import { CanvasEngine } from '@/features/workflow-editor/utils/canvas-engine';
import { type Connection, useReactFlow } from 'reactflow';
import { useUIStore } from '@/stores/ui-store';
import { useNodes } from '@/hooks/nodes/queries';
import {
  getContainingLoop,
  clampToLoopBody,
  calcLoopDims,
  sortNodesParentsFirst,
  LOOP_START_HANDLE_ID,
  LOOP_DIMS,
} from '@/features/workflow-editor/utils/loop-utils';

export const useWorkflow = () => {
  const {
    nodes,
    edges,
    setNodes,
    setEdges,
    onNodesChange,
    onEdgesChange,
    setSelectedNodeId,
  } = useWorkflowStore();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();
  const { setInspectorTab, setSearchOpen } = useUIStore();
  const [mode, setMode] = useState<'select' | 'pan'>('select');
  const { data: nodeRegistry = [] } = useNodes();
  const { removeNode, toggleNodeLock, duplicateNode, updateNodeData, nodes: allNodes } = useWorkflowStore();

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{
    type: 'node' | 'pane'
    x: number
    y: number
    nodeId?: string
  } | null>(null);

  const closeContextMenu = useCallback(() => setContextMenu(null), []);

  const addNode = useCallback(
    (type: string, position: { x: number; y: number }) => {
      const definition = nodeRegistry.find(d => d.type === type);
      const newNode = CanvasEngine.createNode(type, position, definition);
      setNodes(sortNodesParentsFirst([...nodes, newNode]));
      setSelectedNodeId(newNode.id);
      setInspectorTab('Editor');
    },
    [nodes, setNodes, setInspectorTab, setSelectedNodeId, nodeRegistry]
  );

  const onConnect = useCallback(
    (params: Connection) => {
      if (CanvasEngine.validateConnection(params)) {
        setEdges(CanvasEngine.onConnect(params, edges));
      }
    },
    [edges, setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  /** Drop from toolbar — mirrors Sim's handleToolbarDrop */
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const absPos = screenToFlowPosition({ x: event.clientX, y: event.clientY });

      // Is the drop inside a loop container?
      const container = getContainingLoop(absPos, nodes);

      if (container && type !== 'logic.loop') {
        // Relative position, clamped to body area
        const definition = nodeRegistry.find(d => d.type === type);
        const nodeDims = { width: definition?.defaultWidth ?? 200, height: definition?.defaultHeight ?? 80 };
        const rawRel = { x: absPos.x - container.loopPosition.x, y: absPos.y - container.loopPosition.y };
        const relPos = clampToLoopBody(rawRel, container.dims, nodeDims);

        const newNode = CanvasEngine.createNode(type, relPos, definition);
        newNode.parentNode = container.loopId;
        newNode.extent = 'parent';
        if (!newNode.data) newNode.data = { label: '', properties: {} };
        newNode.data.parentId = container.loopId;

        // Auto-connect from Start if this is the first node in the loop
        const existingChildren = nodes.filter(n => n.parentNode === container.loopId);
        let nextEdges = edges;
        if (existingChildren.length === 0) {
          nextEdges = [
            ...edges,
            {
              id: `${container.loopId}-start-${newNode.id}`,
              source: container.loopId,
              sourceHandle: LOOP_START_HANDLE_ID,
              target: newNode.id,
              type: 'smoothstep',
              style: { stroke: 'var(--workflow-edge, #555)', strokeWidth: 2 },
            },
          ];
        }

        // Resize loop to fit new child
        const allChildren = [...existingChildren, newNode];
        const { width: newW, height: newH } = calcLoopDims(allChildren);
        const nextNodes = sortNodesParentsFirst([
          ...nodes.map(n =>
            n.id === container.loopId
              ? { ...n, width: newW, height: newH, style: { ...n.style, width: newW, height: newH }, data: { ...n.data, width: newW, height: newH } }
              : n
          ),
          newNode,
        ]);

        setNodes(nextNodes);
        setEdges(nextEdges);
        setSelectedNodeId(newNode.id);
        setInspectorTab('Editor');
      } else {
        // Normal drop outside loops
        addNode(type, absPos);
      }
    },
    [nodes, edges, setNodes, setEdges, setSelectedNodeId, setInspectorTab, addNode, screenToFlowPosition, nodeRegistry]
  );

  /** Real-time resize + header clamp while dragging a child node */
  const onNodeDrag = useCallback(
    (_event: MouseEvent, draggedNode: any) => {
      if (!draggedNode.parentNode) return;
      const parentLoop = nodes.find(n => n.id === draggedNode.parentNode && n.type === 'logic.loop');
      if (!parentLoop) return;

      const loopDims = {
        width: parentLoop.data?.width ?? parentLoop.width ?? LOOP_DIMS.DEFAULT_WIDTH,
        height: parentLoop.data?.height ?? parentLoop.height ?? LOOP_DIMS.DEFAULT_HEIGHT,
      };
      const nodeDims = { width: draggedNode.width ?? 200, height: draggedNode.height ?? 80 };

      // Clamp to body area — enforces minY so node never enters header zone during drag
      const clampedPos = clampToLoopBody(draggedNode.position, loopDims, nodeDims);
      const needsClamp =
        clampedPos.x !== draggedNode.position.x || clampedPos.y !== draggedNode.position.y;

      // Recalculate loop size using clamped position
      const siblings = nodes.filter(n => n.parentNode === parentLoop.id && n.id !== draggedNode.id);
      const effectiveNode = needsClamp ? { ...draggedNode, position: clampedPos } : draggedNode;
      const allChildren = [...siblings, effectiveNode];
      const { width: newW, height: newH } = calcLoopDims(allChildren);

      const sizeChanged = newW !== loopDims.width || newH !== loopDims.height;
      if (!needsClamp && !sizeChanged) return;

      setNodes(prev =>
        prev.map(n => {
          if (n.id === draggedNode.id && needsClamp) {
            return { ...n, position: clampedPos };
          }
          if (n.id === parentLoop.id && sizeChanged) {
            return { ...n, width: newW, height: newH, style: { ...n.style, width: newW, height: newH }, data: { ...n.data, width: newW, height: newH } };
          }
          return n;
        })
      );
    },
    [nodes, setNodes]
  );

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: any) => {
      setSelectedNodeId(node.id);
      setInspectorTab('Editor');
    },
    [setInspectorTab, setSelectedNodeId]
  );

  /** Drag stop — mirrors Sim's batchUpdateBlocksWithParent */
  const onNodeDragStop = useCallback(
    (_event: MouseEvent, draggedNode: any) => {
      if (draggedNode.type === 'logic.loop') return;

      // Get absolute position of dragged node
      const getAbsPos = (node: any): { x: number; y: number } => {
        if (node.parentNode) {
          const parent = nodes.find(n => n.id === node.parentNode);
          if (parent) {
            return { x: parent.position.x + node.position.x, y: parent.position.y + node.position.y };
          }
        }
        return node.position;
      };

      const absPos = getAbsPos(draggedNode);
      const container = getContainingLoop(absPos, nodes.filter(n => n.id !== draggedNode.id));

      let nextNodes = [...nodes];
      let nextEdges = [...edges];
      let changed = false;

      const currentParent = draggedNode.parentNode;

      if (container && currentParent !== container.loopId) {
        // Dropped INTO a loop (and wasn't already a child of it)
        const nodeDims = { width: draggedNode.width ?? 200, height: draggedNode.height ?? 80 };
        const rawRel = { x: absPos.x - container.loopPosition.x, y: absPos.y - container.loopPosition.y };
        const relPos = clampToLoopBody(rawRel, container.dims, nodeDims);

        nextNodes = nextNodes.map(n =>
          n.id === draggedNode.id
            ? { ...n, parentNode: container.loopId, extent: 'parent' as const, position: relPos, data: { ...n.data, parentId: container.loopId } }
            : n
        );

        // Auto-connect from Start if first node
        const existingChildren = nodes.filter(n => n.parentNode === container.loopId && n.id !== draggedNode.id);
        if (existingChildren.length === 0) {
          const alreadyHasStartEdge = nextEdges.some(
            e => e.source === container.loopId && e.sourceHandle === LOOP_START_HANDLE_ID && e.target === draggedNode.id
          );
          if (!alreadyHasStartEdge) {
            nextEdges = [
              ...nextEdges,
              {
                id: `${container.loopId}-start-${draggedNode.id}`,
                source: container.loopId,
                sourceHandle: LOOP_START_HANDLE_ID,
                target: draggedNode.id,
                type: 'smoothstep',
                style: { stroke: 'var(--workflow-edge, #555)', strokeWidth: 2 },
              },
            ];
          }
        }
        changed = true;
      } else if (!container && currentParent) {
        // Dragged OUT of loop
        const parentLoop = nodes.find(n => n.id === currentParent);
        if (parentLoop) {
          const parentAbs = parentLoop.position;
          const newAbsPos = { x: parentAbs.x + draggedNode.position.x, y: parentAbs.y + draggedNode.position.y };
          nextNodes = nextNodes.map(n =>
            n.id === draggedNode.id
              ? { ...n, parentNode: undefined, extent: undefined, position: newAbsPos, data: { ...n.data, parentId: undefined } }
              : n
          );
          // Remove start edge from this loop to this node
          nextEdges = nextEdges.filter(
            e => !(e.source === currentParent && e.sourceHandle === LOOP_START_HANDLE_ID && e.target === draggedNode.id)
          );
          changed = true;
        }
      } else if (container && currentParent === container.loopId) {
        // Moved within the same loop — just clamp position
        const nodeDims = { width: draggedNode.width ?? 200, height: draggedNode.height ?? 80 };
        const rawRel = draggedNode.position;
        const clampedPos = clampToLoopBody(rawRel, container.dims, nodeDims);
        if (clampedPos.x !== rawRel.x || clampedPos.y !== rawRel.y) {
          nextNodes = nextNodes.map(n =>
            n.id === draggedNode.id ? { ...n, position: clampedPos } : n
          );
          changed = true;
        }
      }

      if (changed) {
        // Resize all affected loop containers
        const loopIds = new Set<string>();
        if (container) loopIds.add(container.loopId);
        if (currentParent) loopIds.add(currentParent);

        for (const loopId of loopIds) {
          const children = nextNodes.filter(n => n.parentNode === loopId);
          const { width: newW, height: newH } = calcLoopDims(children);
          nextNodes = nextNodes.map(n =>
            n.id === loopId
              ? { ...n, width: newW, height: newH, style: { ...n.style, width: newW, height: newH }, data: { ...n.data, width: newW, height: newH } }
              : n
          );
        }

        setNodes(sortNodesParentsFirst(nextNodes));
        setEdges(nextEdges);
      }
    },
    [nodes, edges, setNodes, setEdges]
  );

  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: any) => {
      event.preventDefault()
      setSelectedNodeId(node.id)
      setContextMenu({ type: 'node', x: event.clientX, y: event.clientY, nodeId: node.id })
    },
    [setSelectedNodeId]
  )

  const onPaneContextMenu = useCallback(
    (event: React.MouseEvent) => {
      event.preventDefault()
      setContextMenu({ type: 'pane', x: event.clientX, y: event.clientY })
    },
    []
  )

  const startNodeRename = useCallback(
    (nodeId: string) => {
      setSelectedNodeId(nodeId)
      setInspectorTab('Editor')
      // Small delay to let inspector open before triggering rename
      setTimeout(() => {
        const el = document.querySelector(`[data-rename-trigger="${nodeId}"]`) as HTMLElement
        el?.click()
      }, 100)
    },
    [setSelectedNodeId, setInspectorTab]
  )

  const selectAllNodes = useCallback(() => {
    setNodes(prev => prev.map(n => ({ ...n, selected: true })))
  }, [setNodes])

  const toggleNodeDisabled = useCallback((nodeId: string) => {
    updateNodeData(nodeId, { disabled: !(allNodes.find(n => n.id === nodeId)?.data?.disabled) })
  }, [updateNodeData, allNodes])

  return {
    nodes,
    edges,
    addNode,
    onConnect,
    onNodesChange,
    onEdgesChange,
    onNodeClick,
    onNodeDrag,
    onNodeDragStop,
    onDragOver,
    onDrop,
    onNodeContextMenu,
    onPaneContextMenu,
    contextMenu,
    closeContextMenu,
    removeNode,
    duplicateNode,
    toggleNodeLock,
    toggleNodeDisabled,
    startNodeRename,
    selectAllNodes,
    setSearchOpen,
    reactFlowWrapper,
    mode,
    setMode,
  };
};

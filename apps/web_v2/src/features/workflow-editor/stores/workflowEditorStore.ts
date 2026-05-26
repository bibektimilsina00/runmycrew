import { create } from "zustand";
import type { Node, Edge } from "reactflow";
import type { NodeDefinition } from "../types/editorTypes";
import type { SaveState, WorkflowDetail } from "../types/editorTypes";

interface WorkflowEditorState {
  // Loaded workflow meta
  workflow: WorkflowDetail | null;
  setWorkflow: (w: WorkflowDetail) => void;

  // Node definitions loaded from API
  nodeDefinitions: NodeDefinition[];
  setNodeDefinitions: (defs: NodeDefinition[]) => void;

  // ReactFlow graph state
  nodes: Node[];
  edges: Edge[];
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: ((changes: unknown[]) => void) | null;
  onEdgesChange: ((changes: unknown[]) => void) | null;

  // Node mutations
  removeNode: (id: string) => void;
  toggleNodeLock: (id: string) => void;
  duplicateNode: (id: string) => void;
  toggleNodeHandleDirection: (id: string) => void;

  // Save state
  saveState: SaveState;
  setSaveState: (s: SaveState) => void;
  versionVector: number;
  setVersionVector: (v: number) => void;

  // UI state
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;
  inspectorOpen: boolean;
  setInspectorOpen: (open: boolean) => void;
  inspectorTab: "config" | "copilot" | "library" | "logs" | "test";
  setInspectorTab: (tab: WorkflowEditorState["inspectorTab"]) => void;
  workflowLocked: boolean;
  toggleWorkflowLock: () => void;

  // Reset when leaving editor
  reset: () => void;
}

export const useWorkflowEditorStore = create<WorkflowEditorState>(
  (set, get) => ({
    workflow: null,
    setWorkflow: (workflow) => set({ workflow }),

    nodeDefinitions: [],
    setNodeDefinitions: (nodeDefinitions) => set({ nodeDefinitions }),

    nodes: [],
    edges: [],
    setNodes: (nodes) => set({ nodes }),
    setEdges: (edges) => set({ edges }),
    onNodesChange: null,
    onEdgesChange: null,

    removeNode: (id) =>
      set((s) => ({
        nodes: s.nodes.filter((n) => n.id !== id),
        edges: s.edges.filter((e) => e.source !== id && e.target !== id),
        saveState: "unsaved" as SaveState,
      })),

    toggleNodeLock: (id) =>
      set((s) => ({
        nodes: s.nodes.map((n) =>
          n.id === id
            ? { ...n, data: { ...n.data, locked: !n.data?.locked } }
            : n,
        ),
        saveState: "unsaved" as SaveState,
      })),

    duplicateNode: (id) => {
      const node = get().nodes.find((n) => n.id === id);
      if (!node) return;
      const newNode: Node = {
        ...node,
        id: crypto.randomUUID(),
        position: { x: node.position.x + 30, y: node.position.y + 30 },
        selected: false,
      };
      set((s) => ({
        nodes: [...s.nodes, newNode],
        saveState: "unsaved" as SaveState,
      }));
    },

    toggleNodeHandleDirection: (id) =>
      set((s) => ({
        nodes: s.nodes.map((n) =>
          n.id === id
            ? {
                ...n,
                data: {
                  ...n.data,
                  handleDirection:
                    n.data?.handleDirection === "vertical"
                      ? "horizontal"
                      : "vertical",
                },
              }
            : n,
        ),
        saveState: "unsaved" as SaveState,
      })),

    saveState: "saved",
    setSaveState: (saveState) => set({ saveState }),
    versionVector: 0,
    setVersionVector: (versionVector) => set({ versionVector }),

    selectedNodeId: null,
    setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
    inspectorOpen: false,
    setInspectorOpen: (inspectorOpen) => set({ inspectorOpen }),
    inspectorTab: "config",
    setInspectorTab: (inspectorTab) => set({ inspectorTab }),
    workflowLocked: false,
    toggleWorkflowLock: () =>
      set((s) => ({ workflowLocked: !s.workflowLocked })),

    reset: () =>
      set({
        workflow: null,
        nodes: [],
        edges: [],
        nodeDefinitions: [],
        saveState: "saved",
        versionVector: 0,
        selectedNodeId: null,
        inspectorOpen: false,
        inspectorTab: "config",
        workflowLocked: false,
      }),
  }),
);

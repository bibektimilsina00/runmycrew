import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type EditorTab = 'copilot' | 'library' | 'config' | 'logs' | 'test'
export type PanelZone = 'right' | 'bottom'

const TAB_LOCKED_ZONES: Partial<Record<EditorTab, PanelZone>> = {
  logs: 'bottom',
}

const DEFAULT_ZONES: Record<EditorTab, PanelZone> = {
  copilot: 'right',
  library: 'right',
  config: 'right',
  test: 'right',
  logs: 'bottom',
}

const MIN_BOTTOM_HEIGHT = 140
const MAX_BOTTOM_HEIGHT = 640
const DEFAULT_BOTTOM_HEIGHT = 260

/**
 * UI-only state attached to a node. Lives here instead of `node.data` so it
 * never leaks into the saved workflow graph (which is sent to the backend
 * and shared between users).
 *
 * - `showAdvanced` — whether the node body + inspector reveal "advanced" props.
 */
export interface NodeUIState {
  showAdvanced?: boolean
}

interface EditorLayoutState {
  panelZones: Record<EditorTab, PanelZone>
  rightActiveTab: EditorTab
  bottomActiveTab: EditorTab
  rightOpen: boolean
  bottomOpen: boolean
  bottomHeight: number

  // Inspector's upstream-inputs section: independent collapse + height so
  // the inputs preview no longer follows the bottom Logs panel's state.
  inspectorInputsOpen: boolean
  inspectorInputsHeight: number

  // Per-node UI prefs (volatile across workflows; not persisted to graph).
  nodeUI: Record<string, NodeUIState>

  setRightActiveTab: (tab: EditorTab) => void
  setBottomActiveTab: (tab: EditorTab) => void
  setZoneOpen: (zone: PanelZone, open: boolean) => void
  toggleZone: (zone: PanelZone) => void
  setBottomHeight: (px: number) => void
  moveTabToZone: (tab: EditorTab, zone: PanelZone) => void
  focusTab: (tab: EditorTab) => void
  closeTabPanel: (tab: EditorTab) => void
  tabsInZone: (zone: PanelZone) => EditorTab[]

  toggleInspectorInputs: () => void
  setInspectorInputsHeight: (px: number) => void

  setNodeShowAdvanced: (nodeId: string, value: boolean) => void
  clearNodeUI: (nodeId: string) => void
}

export const useEditorLayoutStore = create<EditorLayoutState>()(
  persist(
    (set, get) => ({
      panelZones: { ...DEFAULT_ZONES },
      rightActiveTab: 'copilot',
      bottomActiveTab: 'logs',
      rightOpen: true,
      bottomOpen: false,
      bottomHeight: DEFAULT_BOTTOM_HEIGHT,
      inspectorInputsOpen: false,
      inspectorInputsHeight: 240,
      nodeUI: {},

      setRightActiveTab: (rightActiveTab) => set({ rightActiveTab, rightOpen: true }),
      setBottomActiveTab: (bottomActiveTab) => set({ bottomActiveTab, bottomOpen: true }),

      setZoneOpen: (zone, open) =>
        set(zone === 'right' ? { rightOpen: open } : { bottomOpen: open }),

      toggleZone: (zone) =>
        set((s) =>
          zone === 'right' ? { rightOpen: !s.rightOpen } : { bottomOpen: !s.bottomOpen },
        ),

      setBottomHeight: (px) =>
        set({
          bottomHeight: Math.min(MAX_BOTTOM_HEIGHT, Math.max(MIN_BOTTOM_HEIGHT, Math.round(px))),
        }),

      moveTabToZone: (tab, zone) => {
        const lock = TAB_LOCKED_ZONES[tab]
        if (lock && lock !== zone) return
        const s = get()
        if (s.panelZones[tab] === zone) return
        set({
          panelZones: { ...s.panelZones, [tab]: zone },
          ...(zone === 'right'
            ? { rightActiveTab: tab, rightOpen: true }
            : { bottomActiveTab: tab, bottomOpen: true }),
        })
      },

      focusTab: (tab) => {
        const zone = get().panelZones[tab]
        set(
          zone === 'right'
            ? { rightActiveTab: tab, rightOpen: true }
            : { bottomActiveTab: tab, bottomOpen: true },
        )
      },

      closeTabPanel: (tab) => {
        const zone = get().panelZones[tab]
        set(zone === 'right' ? { rightOpen: false } : { bottomOpen: false })
      },

      tabsInZone: (zone) => {
        const z = get().panelZones
        return (Object.keys(z) as EditorTab[]).filter((t) => z[t] === zone)
      },

      toggleInspectorInputs: () =>
        set((s) => ({ inspectorInputsOpen: !s.inspectorInputsOpen })),

      setInspectorInputsHeight: (px) =>
        set({
          // Same clamp range as the bottom panel for visual rhythm — the
          // section sits in the inspector pane so its max stays modest.
          inspectorInputsHeight: Math.min(
            MAX_BOTTOM_HEIGHT,
            Math.max(MIN_BOTTOM_HEIGHT, Math.round(px)),
          ),
        }),

      setNodeShowAdvanced: (nodeId, value) =>
        set((s) => ({
          nodeUI: {
            ...s.nodeUI,
            [nodeId]: { ...s.nodeUI[nodeId], showAdvanced: value },
          },
        })),

      clearNodeUI: (nodeId) =>
        set((s) => {
          const { [nodeId]: _omit, ...rest } = s.nodeUI
          return { nodeUI: rest }
        }),
    }),
    {
      name: 'runmycrew-editor-layout',
      version: 1,
      partialize: (s) => ({
        panelZones: s.panelZones,
        rightActiveTab: s.rightActiveTab,
        bottomActiveTab: s.bottomActiveTab,
        rightOpen: s.rightOpen,
        bottomHeight: s.bottomHeight,
        // bottomOpen intentionally NOT persisted — the logs panel is
        // hidden on every fresh session and only opens when the user
        // explicitly clicks the tab or runs the workflow.
        inspectorInputsOpen: s.inspectorInputsOpen,
        inspectorInputsHeight: s.inspectorInputsHeight,
      }),
      merge: (persisted, current) => {
        const p = (persisted ?? {}) as Partial<EditorLayoutState>
        // Always enforce locked zones — guard against stale persisted state.
        const zones: Record<EditorTab, PanelZone> = {
          ...DEFAULT_ZONES,
          ...(p.panelZones ?? {}),
        }
        for (const [tab, lockedZone] of Object.entries(TAB_LOCKED_ZONES) as [
          EditorTab,
          PanelZone,
        ][]) {
          zones[tab] = lockedZone
        }
        // Force bottomOpen to default (false) even if a pre-v2 persisted
        // payload still has it — covers users who upgrade with the panel
        // open in localStorage.
        return { ...current, ...p, panelZones: zones, bottomOpen: false }
      },
    },
  ),
)

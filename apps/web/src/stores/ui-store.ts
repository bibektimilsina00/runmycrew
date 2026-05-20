import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type InspectorTabType = 'Copilot' | 'Toolbar' | 'Editor'
export type LogViewMode = 'structured' | 'raw'
export type ThemeMode = 'dark' | 'light' | 'system'

interface UIState {
  inspectorTab: InspectorTabType
  setInspectorTab: (tab: InspectorTabType) => void
  isSidebarCollapsed: boolean
  toggleSidebar: () => void
  isSearchOpen: boolean
  setSearchOpen: (open: boolean) => void
  // Log inspector view preferences
  logViewMode: LogViewMode
  setLogViewMode: (mode: LogViewMode) => void
  logWrapView: boolean
  setLogWrapView: (wrap: boolean) => void
  logOpenOnRun: boolean
  setLogOpenOnRun: (open: boolean) => void
  // Theme
  theme: ThemeMode
  setTheme: (theme: ThemeMode) => void
  // Copilot panel state
  copilotView: 'chat' | 'history'
  setCopilotView: (view: 'chat' | 'history') => void
  copilotNewChatTrigger: number
  triggerCopilotNewChat: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      inspectorTab: 'Editor',
      setInspectorTab: (tab) => set({ inspectorTab: tab }),
      isSidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
      isSearchOpen: false,
      setSearchOpen: (open) => set({ isSearchOpen: open }),
      logViewMode: 'structured',
      setLogViewMode: (mode) => set({ logViewMode: mode }),
      logWrapView: false,
      setLogWrapView: (wrap) => set({ logWrapView: wrap }),
      logOpenOnRun: true,
      setLogOpenOnRun: (open) => set({ logOpenOnRun: open }),
      theme: 'dark',
      setTheme: (theme) => set({ theme }),
      copilotView: 'chat',
      setCopilotView: (view) => set({ copilotView: view }),
      copilotNewChatTrigger: 0,
      triggerCopilotNewChat: () => set((s) => ({ copilotNewChatTrigger: s.copilotNewChatTrigger + 1 })),
    }),
    {
      name: 'fuse-ui',
      partialState: (state) => ({ theme: state.theme }),
    } as any,
  ),
)

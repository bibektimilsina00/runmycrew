import { create } from 'zustand'

/**
 * Tiny handoff for prompts created outside the Copilot panel (e.g. the
 * dashboard generator). The setter parks a prompt before navigation; the
 * Copilot hook consumes it on mount.
 */
interface CopilotPendingState {
  prompt: string | null
  set: (prompt: string | null) => void
  consume: () => string | null
}

export const useCopilotPendingStore = create<CopilotPendingState>((set, get) => ({
  prompt: null,
  set: (prompt) => set({ prompt }),
  consume: () => {
    const p = get().prompt
    if (p) set({ prompt: null })
    return p
  },
}))

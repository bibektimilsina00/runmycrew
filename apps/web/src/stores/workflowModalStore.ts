import { create } from 'zustand'

interface WorkflowModalStore {
  pendingOpen: boolean
  requestOpen: () => void
  consume: () => void
}

export const useWorkflowModalStore = create<WorkflowModalStore>(set => ({
  pendingOpen: false,
  requestOpen: () => set({ pendingOpen: true }),
  consume: () => set({ pendingOpen: false }),
}))

import { create } from 'zustand'

interface TablesState {
  selectedTableId: string | null
  setSelectedTableId: (id: string | null) => void
}

export const useTablesStore = create<TablesState>((set) => ({
  selectedTableId: null,
  setSelectedTableId: (id) => set({ selectedTableId: id }),
}))

import { useEffect } from 'react'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'

// Keyboard shortcuts for the editor canvas: undo/redo, copy/paste, select-all,
// delete. No-ops while typing in an input/textarea/contenteditable.
export function useEditorShortcuts() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null
      const tag = target?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable) return

      const mod = e.metaKey || e.ctrlKey
      const key = e.key.toLowerCase()
      const store = useWorkflowEditorStore.getState()

      if (mod && key === 'z') {
        e.preventDefault()
        if (e.shiftKey) store.redo()
        else store.undo()
        return
      }
      if (mod && key === 'y') { e.preventDefault(); store.redo(); return }
      if (mod && key === 'c') { store.copySelection(); return }
      if (mod && key === 'v') { store.paste(); return }
      if (mod && key === 'a') { e.preventDefault(); store.selectAll(); return }
      if (key === 'delete' || key === 'backspace') { e.preventDefault(); store.deleteSelected(); return }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])
}

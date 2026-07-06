import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'
import { editorAPI } from '../../services/editorAPI'

/**
 * Crew-only editable description. Rendered under the action row in crew mode
 * (see EditorActionBar). Self-contained: reads the loaded crew from the shared
 * editor store, persists on blur via PUT /crews/{id}, and writes the returned
 * crew back into the store so the value survives re-renders. Only shown for
 * crews, so the workflow top bar is untouched.
 */
export function CrewDescriptionField() {
  const workflow    = useWorkflowEditorStore((s) => s.workflow)
  const setWorkflow = useWorkflowEditorStore((s) => s.setWorkflow)
  const [value, setValue] = useState(workflow?.description ?? '')

  // Re-sync when a different crew loads (or the server value changes).
  useEffect(() => {
    setValue(workflow?.description ?? '')
  }, [workflow?.id, workflow?.description])

  const mutation = useMutation({
    mutationFn: (description: string) => editorAPI.updateDescription(workflow?.id ?? '', description),
    onSuccess: (updated) => setWorkflow(updated),
  })

  const commit = () => {
    const next = value.trim()
    if (!workflow || next === (workflow.description ?? '')) return
    mutation.mutate(next)
  }

  return (
    <div className="px-3 pb-2.5">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === 'Enter') e.currentTarget.blur()
          if (e.key === 'Escape') { setValue(workflow?.description ?? ''); e.currentTarget.blur() }
        }}
        placeholder="Add a crew description…"
        className="w-full rounded-[7px] border border-[var(--border-faint)] bg-[var(--surface)] px-2.5 py-1.5 text-[12px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none transition-colors focus:border-[var(--border)]"
      />
    </div>
  )
}

import React, { useState } from 'react'
import { History, RotateCcw, X, Loader2 } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { requestJson } from '@/lib/api/client'
import { useWorkflowStore } from '@/stores/workflow-store'
import { cn } from '@/lib/utils'

const VersionSchema = z.object({
  id: z.string(),
  version: z.number(),
  label: z.string().nullable().optional(),
  created_at: z.string(),
})
type Version = z.infer<typeof VersionSchema>

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60_000) return 'just now'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

/** Standalone panel — used inside WorkflowOptionsMenu */
export const VersionHistoryPanel: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [restoringId, setRestoringId] = useState<string | null>(null)
  const { workflowId } = useWorkflowStore()
  const queryClient = useQueryClient()

  const { data: versions = [], isLoading } = useQuery({
    queryKey: ['workflow-versions', workflowId],
    queryFn: () => requestJson(z.array(VersionSchema), {
      url: `/workflows/${workflowId}/versions`,
      method: 'GET',
    }),
    enabled: !!workflowId,
    staleTime: 10_000,
  })

  const restore = useMutation({
    mutationFn: async (versionId: string) => {
      setRestoringId(versionId)
      return requestJson(z.any(), {
        url: `/workflows/${workflowId}/versions/${versionId}/restore`,
        method: 'POST',
      })
    },
    onSuccess: (data) => {
      useWorkflowStore.getState().loadWorkflow(data)
      queryClient.invalidateQueries({ queryKey: ['workflow-versions', workflowId] })
      onClose()
    },
    onSettled: () => setRestoringId(null),
  })

  if (!workflowId) return null

  return (
    <div className="w-[280px] rounded-xl border border-[var(--border-default)] bg-[var(--surface-2)] shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 fixed z-[9999]"
      style={{ right: 12, top: 50 }}>
      <div className="flex items-center justify-between px-3 py-2.5 border-b border-[var(--border-default)]">
        <span className="text-[12px] font-semibold text-white">Version History</span>
        <button onClick={onClose} className="text-[var(--text-muted)] hover:text-white transition-colors">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="max-h-72 overflow-y-auto custom-scrollbar">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-4 h-4 animate-spin text-[var(--text-muted)]" />
          </div>
        ) : versions.length === 0 ? (
          <p className="px-4 py-6 text-[12px] text-[var(--text-muted)] text-center italic">
            No saved versions yet.<br />Versions are created automatically on each save.
          </p>
        ) : (
          versions.map((v: Version) => (
            <div key={v.id} className="flex items-center justify-between px-3 py-2.5 border-b border-[var(--border-default)] last:border-0 group hover:bg-[var(--surface-3)] transition-colors">
              <div className="min-w-0">
                <p className="text-[12px] text-white font-medium">v{v.version} {v.label && `— ${v.label}`}</p>
                <p className="text-[11px] text-[var(--text-muted)]">{formatTime(v.created_at)}</p>
              </div>
              <button
                onClick={() => restore.mutate(v.id)}
                disabled={restoringId === v.id}
                className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-[var(--text-muted)] hover:text-white hover:bg-[var(--surface-4)] transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50"
                title="Restore this version"
              >
                {restoringId === v.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
                Restore
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

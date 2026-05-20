import { useNavigate, useParams } from 'react-router-dom'
import { useAcceptInvite, useInvitePreview } from '@/features/workspaces/hooks'

export function InviteAcceptPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const preview = useInvitePreview(token)
  const accept = useAcceptInvite(token)

  return (
    <div className="flex h-full items-center justify-center bg-[var(--bg)] p-6 text-white">
      <div className="w-full max-w-md space-y-4 rounded-lg border border-[var(--border-default)] bg-[var(--surface-1)] p-6">
        <div>
          <p className="text-[12px] uppercase text-[var(--text-muted)]">Workspace Invite</p>
          <h1 className="text-xl font-semibold">
            {preview.data ? preview.data.workspace_name : 'Loading invite'}
          </h1>
        </div>
        {preview.data && (
          <p className="text-sm text-[var(--text-muted)]">
            Join as <span className="text-white">{preview.data.role}</span> using {preview.data.email}.
          </p>
        )}
        <button
          disabled={!preview.data || accept.isPending}
          onClick={() => accept.mutate(undefined, {
            onSuccess: () => {
              // useAcceptInvite already refetches workspace list and updates the store
              // Navigate after a short tick to let store update settle
              setTimeout(() => navigate('/settings/team'), 100)
            },
          })}
          className="w-full rounded bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
        >
          Accept Invite
        </button>
        {accept.error && <p className="text-sm text-red-400">Unable to accept invite.</p>}
      </div>
    </div>
  )
}

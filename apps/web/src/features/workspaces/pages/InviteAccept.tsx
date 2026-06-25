import { useParams, useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useInvitePreview, useAcceptInvite } from '../hooks/useWorkspace'
import { APP_ROUTES } from '@/shared/constants/routes'
import { cn } from '@/lib/cn'

export function InviteAccept() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const { data: preview, isLoading, isError } = useInvitePreview(token)
  const accept = useAcceptInvite(token)

  const handleAccept = async () => {
    if (!isAuthenticated) {
      navigate(`${APP_ROUTES.LOGIN}?redirect=/invites/${token}`)
      return
    }
    await accept.mutateAsync()
    navigate(APP_ROUTES.DASHBOARD)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg)] p-6">
        <div className="w-full max-w-[420px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[12px] pt-[36px] px-[32px] pb-[32px] flex flex-col items-center gap-[14px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.5)] text-center">
          <div className="w-[28px] h-[28px] border-2 border-[var(--border)] border-t-[var(--text)] rounded-full animate-spin" />
          <p className="text-[13px] text-[var(--text-faint)] m-0">Loading invite…</p>
        </div>
      </div>
    )
  }

  if (isError || !preview) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg)] p-6">
        <div className="w-full max-w-[420px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[12px] pt-[36px] px-[32px] pb-[32px] flex flex-col items-center gap-[14px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.5)] text-center">
          <div className="w-[48px] h-[48px] rounded-[12px] bg-[oklch(0.70_0.18_22/0.12)] flex items-center justify-center text-[var(--err)]">
            <Icons.Activity style={{ width: 24, height: 24 }} />
          </div>
          <h2 className="text-[20px] font-medium tracking-tight text-[var(--text)] m-0">Invalid or expired invite</h2>
          <p className="text-[14px] text-[var(--text-mute)] m-0 flex items-center justify-center gap-[8px]">
            This invite link is no longer valid. Ask the workspace admin to send a new one.
          </p>
          <button
            className="w-full p-[11px] rounded-[10px] bg-[var(--accent)] text-white text-[14px] font-semibold border-none cursor-pointer transition-colors duration-120 hover:brightness-110 disabled:opacity-50 disabled:cursor-default"
            onClick={() => navigate(APP_ROUTES.DASHBOARD)}
          >
            Go to dashboard
          </button>
        </div>
      </div>
    )
  }

  const alreadyAccepted = !!preview.accepted_at

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg)] p-6">
      <div className="w-full max-w-[420px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[12px] pt-[36px] px-[32px] pb-[32px] flex flex-col items-center gap-[14px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.5)] text-center">
        <div className="w-[56px] h-[56px] rounded-[10px] bg-[var(--text)] text-[var(--bg)] flex items-center justify-center text-[22px] font-bold tracking-tight">
          {preview.workspace_name[0]?.toUpperCase()}
        </div>
        <h2 className="text-[20px] font-medium tracking-tight text-[var(--text)] m-0">
          Join <strong className="font-bold">{preview.workspace_name}</strong>
        </h2>
        <p className="text-[14px] text-[var(--text-mute)] m-0 flex items-center justify-center gap-[8px]">
          You've been invited as{' '}
          <span className={cn(
            "font-mono text-[10px] tracking-widest uppercase py-[3px] px-[8px] pb-[2px] rounded-[5px] font-semibold",
            preview.role === 'owner' && "bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]",
            preview.role === 'admin' && "bg-[oklch(0.78_0.13_245/0.14)] text-[var(--accent)]",
            preview.role === 'member' && "bg-[var(--surface-2)] text-[var(--text-mute)]",
            preview.role === 'viewer' && "bg-[var(--surface)] text-[var(--text-dim)]"
          )}>
            {preview.role}
          </span>
        </p>
        <p className="text-[12.5px] text-[var(--text-faint)] m-0">
          Invite sent to <strong className="text-[var(--text-mute)]">{preview.email}</strong>
        </p>

        {alreadyAccepted ? (
          <>
            <div className="flex items-center gap-[7px] text-[13px] font-medium text-[var(--ok)]">
              <Icons.Check style={{ width: 14, height: 14, color: 'var(--ok)' }} />
              Already accepted
            </div>
            <button
              className="w-full p-[11px] rounded-[10px] bg-[var(--accent)] text-white text-[14px] font-semibold border-none cursor-pointer transition-colors duration-120 hover:brightness-110 disabled:opacity-50 disabled:cursor-default"
              onClick={() => navigate(APP_ROUTES.DASHBOARD)}
            >
              Go to workspace
            </button>
          </>
        ) : (
          <>
            {!isAuthenticated && (
              <p className="text-[12.5px] text-[var(--text-faint)] m-0 max-w-[300px]">
                You'll need to sign in or create an account to accept this invite.
              </p>
            )}
            <button
              className="w-full p-[11px] rounded-[10px] bg-[var(--accent)] text-white text-[14px] font-semibold border-none cursor-pointer transition-colors duration-120 hover:brightness-110 disabled:opacity-50 disabled:cursor-default"
              onClick={handleAccept}
              disabled={accept.isPending}
            >
              {accept.isPending ? 'Joining…' : isAuthenticated ? 'Accept invite' : 'Sign in to accept'}
            </button>
            {accept.isError && (
              <p className="text-[12.5px] text-[var(--err)] m-0">{accept.error?.message ?? 'Something went wrong'}</p>
            )}
          </>
        )}

        <p className="text-[11px] font-mono text-[var(--text-dim)] mt-[4px]">
          Expires {new Date(preview.expires_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
        </p>
      </div>
    </div>
  )
}

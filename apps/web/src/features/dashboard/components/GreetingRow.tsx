import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { Icons } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkflowModalStore } from '@/stores/workflowModalStore'

export function GreetingRow() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const requestCreateWorkflow = useWorkflowModalStore(s => s.requestOpen)

  const formattedDate = new Date()
    .toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
    .toUpperCase()

  const hour = new Date().getHours()
  const greeting =
    hour < 12 ? 'Good morning' :
    hour < 17 ? 'Good afternoon' :
                'Good evening'

  const firstName = user?.full_name ? user.full_name.split(' ')[0] : (user?.email?.split('@')[0] ?? '')

  return (
    <div className="flex flex-col gap-[18px]">
      <div className="flex items-center gap-[8px]">
        <span className="relative inline-flex w-[8px] h-[8px]">
          <span className="absolute inset-0 rounded-full bg-[var(--ok)] animate-[fusePulse_2.4s_ease-in-out_infinite]" />
        </span>
        <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-faint)]">ALL SYSTEMS OPERATIONAL</span>
        <span className="text-[var(--text-dim)]">·</span>
        <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-dim)]">{formattedDate}</span>
      </div>

      <div className="flex items-end justify-between gap-[16px] flex-wrap">
        <h1 className="m-0 text-[27px] font-semibold tracking-[-0.022em] text-[var(--text)] flex-1 min-w-[280px]">
          {greeting}, {firstName}
        </h1>
        <div className="flex items-center gap-[9px] shrink-0">
          <button
            onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
            className="inline-flex items-center gap-[7px] py-[8px] px-[14px] rounded-[6px] text-[13px] font-medium text-[var(--text)] bg-[rgba(255,255,255,0.02)] border border-[var(--border-soft)] transition-colors hover:bg-[rgba(255,255,255,0.05)] hover:border-[var(--border)] [&_svg]:w-[15px] [&_svg]:h-[15px]"
          >
            <Icons.Plug />
            Connect app
          </button>
          <button
            onClick={requestCreateWorkflow}
            className="inline-flex items-center gap-[7px] py-[8px] px-[14px] rounded-[6px] text-[13px] font-semibold text-white bg-[var(--accent)] border border-transparent transition-[filter] hover:brightness-110 [&_svg]:w-[15px] [&_svg]:h-[15px]"
          >
            <Icons.Plus />
            New automation
          </button>
        </div>
      </div>
    </div>
  )
}

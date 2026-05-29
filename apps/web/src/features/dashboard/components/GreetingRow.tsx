import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { Icons } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkflowModalStore } from '@/stores/workflowModalStore'

export function GreetingRow() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const requestCreateWorkflow = useWorkflowModalStore(s => s.requestOpen)

  const formattedDate = new Date().toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  })

  const hour = new Date().getHours()
  const greeting =
    hour < 12 ? 'Good morning' :
    hour < 17 ? 'Good afternoon' :
                'Good evening'

  const firstName = user?.full_name ? user.full_name.split(' ')[0] : (user?.email?.split('@')[0] ?? '')

  return (
    <div className="flex items-end justify-between gap-[24px]">
      <div className="flex flex-col">
        <span className="inline-flex items-center gap-[8px] font-mono text-[10.5px] tracking-widest uppercase text-[var(--text-faint)] font-medium">
          <span className="w-[6px] h-[6px] rounded-full bg-[var(--ok)] shadow-[0_0_6px_oklch(0.78_0.14_145/0.6)]" />
          All systems operational · {formattedDate}
        </span>
        <h1 className="text-[26px] mt-[6px] font-medium tracking-tight">
          {greeting}, {firstName}
          <span style={{ color: 'var(--accent)' }}>.</span>
        </h1>
      </div>
      <div className="flex items-center gap-[8px]">
        <button
          className="inline-flex items-center gap-[7px] py-[8px] px-[14px] rounded-[9px] text-[13px] font-medium bg-[var(--surface)] border border-[var(--border-faint)] text-[var(--text)] hover:bg-[var(--surface-2)] transition-colors"
          onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
        >
          <Icons.Plug className="w-3.5 h-3.5" />
          Connect app
        </button>
        <button
          className="inline-flex items-center gap-[7px] py-[8px] px-[14px] rounded-[9px] text-[13px] font-medium bg-[var(--text)] text-[var(--bg)] border border-[var(--text)] hover:bg-[oklch(0.90_0.003_250)] transition-colors"
          onClick={requestCreateWorkflow}
        >
          <Icons.Plus className="w-3.5 h-3.5" />
          New automation
        </button>
      </div>
    </div>
  )
}

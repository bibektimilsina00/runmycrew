import { useAuth } from '@/features/auth/hooks/useAuth'
import { Icons } from '@/shared/components'

interface GreetingRowProps {
  onNewAutomation: () => void
  onConnectApp: () => void
}

export function GreetingRow({ onNewAutomation, onConnectApp }: GreetingRowProps) {
  const { user } = useAuth()

  const formattedDate = new Date().toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  })

  const hour = new Date().getHours()
  let greetingText = 'Good morning'
  if (hour >= 12 && hour < 17) greetingText = 'Good afternoon'
  else if (hour >= 17 || hour < 4) greetingText = 'Good evening'

  const firstName = user?.full_name ? user.full_name.split(' ')[0] : 'Mahesh'

  return (
    <div className="flex items-end justify-between gap-[24px]">
      <div className="flex flex-col">
        <span className="inline-flex items-center gap-[8px] font-mono text-[10.5px] tracking-widest uppercase text-[var(--text-faint)] font-medium">
          <span className={`w-[6px] h-[6px] rounded-full bg-[var(--ok)] shadow-[0_0_6px_oklch(0.78_0.14_145/0.6)] animate-status-pulse`} />
          All systems operational · {formattedDate}
        </span>
        <h1 className="text-[26px] mt-[6px] font-medium tracking-tight">
          {greetingText}, {firstName}
          <span style={{ color: 'var(--accent)' }}>.</span>
        </h1>
      </div>
      <div className="flex items-center gap-[8px]">
        <button className={`inline-flex items-center gap-[7px] py-[8px] px-[14px] rounded-[9px] text-[13px] font-medium transition-colors duration-120 bg-[var(--surface)] border border-[var(--border-faint)] text-[var(--text)] hover:bg-[var(--surface-2)]`} onClick={onConnectApp}>
          <Icons.Plug className="w-3.5 h-3.5" />
          <span>Connect app</span>
        </button>
        <button className={`inline-flex items-center gap-[7px] py-[8px] px-[14px] rounded-[9px] text-[13px] font-medium transition-colors duration-120 bg-[var(--text)] text-[var(--bg)] border border-[var(--text)] hover:bg-[oklch(0.90_0.003_250)]`} onClick={onNewAutomation}>
          <Icons.Plus className="w-3.5 h-3.5" />
          <span>New automation</span>
        </button>
      </div>
    </div>
  )
}

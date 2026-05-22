import { useToast } from '@/shared/components'
import { GreetingRow } from '../components/GreetingRow'
import { StatsGrid } from '../components/StatsGrid'
import { PromptCard } from '../components/PromptCard'
import { RecentRuns } from '../components/RecentRuns'
import type { RunItem } from '../components/RecentRuns'
import { SchedulePanel } from '../components/SchedulePanel'
import type { ScheduleItem } from '../components/SchedulePanel'
import { ConnectionsPanel } from '../components/ConnectionsPanel'

export function Dashboard() {
  const { toast } = useToast()

  const handleNewAutomation = () => {
    toast('New automation draft', {
      variant: 'ok',
      description: 'Created a new Untitled automation flow.',
    })
  }

  const handleConnectApp = () => {
    toast('Connect app integration', {
      variant: 'ok',
      description: 'Redirecting to connection integrations catalog...',
    })
  }

  const handlePromptSubmit = (prompt: string, mode: 'flow' | 'agent') => {
    toast(`Drafting ${mode} automation`, {
      variant: 'ok',
      description: prompt
        ? `Fuse AI is designing "${prompt.slice(0, 40)}..." using Filament 2.`
        : 'Fuse AI is opening an empty workspace layout.',
    })
  }

  const handleOpenRun = (run: RunItem, index: number) => {
    toast(`Viewing run details`, {
      variant: 'ok',
      description: `Opening execution logs for run #${index + 1}: ${run.name}`,
    })
  }

  const handleOpenSchedule = (item: ScheduleItem) => {
    toast(`Scheduled task details`, {
      variant: 'ok',
      description: `Opening schedule config for: ${item.name}`,
    })
  }

  return (
    <div className="p-[24px_28px_28px] flex flex-col gap-[24px] max-w-[1240px] w-full mx-auto flex-1">
      <GreetingRow onNewAutomation={handleNewAutomation} onConnectApp={handleConnectApp} />
      <StatsGrid />
      <PromptCard onSubmit={handlePromptSubmit} />
      <div className="grid grid-cols-[minmax(0,1fr)_320px] gap-[24px]">
        <RecentRuns
          onOpenRun={handleOpenRun}
          onViewAll={() => toast('Recent runs overview', { description: 'Opening full streaming execution feeds logs...' })}
        />
        <div className="flex flex-col gap-[16px]">
          <SchedulePanel
            onOpenSchedule={handleOpenSchedule}
            onViewAll={() => toast('All schedules overview', { description: 'Showing weekly scheduled rotations...' })}
          />
          <ConnectionsPanel onManageConnections={handleConnectApp} />
        </div>
      </div>
    </div>
  )
}

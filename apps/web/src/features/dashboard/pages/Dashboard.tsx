import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GreetingRow }      from '../components/GreetingRow'
import { StatsGrid }        from '../components/StatsGrid'
import { PromptCard }       from '../components/PromptCard'
import { SuggestionChips }  from '../components/SuggestionChips'
import { RecentRuns }       from '../components/RecentRuns'
import { SchedulePanel }    from '../components/SchedulePanel'
import { ConnectionsPanel } from '../components/ConnectionsPanel'
import { useDashboard }     from '../hooks/useDashboard'
import { useAIGenerator }   from '../hooks/useAIGenerator'
import { APP_ROUTES }       from '@/shared/constants/routes'
import type { DashboardStat } from '../services/dashboardAPI'

const SKELETON_STATS: DashboardStat[] = [
  { label: 'Runs today',       value: '—', unit: '',   delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Success rate',     value: '—', unit: '%',  delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Time saved',       value: '—', unit: 'hr', delta: '—', delta_dir: 'flat', spark: [] },
  { label: 'Active workflows', value: '—', unit: '',   delta: '—', delta_dir: 'flat', spark: [] },
]

const SUGGESTIONS = [
  'Every weekday at 9am, summarize new GitHub issues and post to Slack',
  'When a new row is added to Notion, send a welcome email',
  'Fetch JSON from an API and save it to a database',
]

export function Dashboard() {
  const navigate = useNavigate()
  const { data } = useDashboard()
  const ai = useAIGenerator()
  const [prompt, setPrompt] = useState('')
  const [kind, setKind] = useState<'workflow' | 'crew'>('workflow')

  const stats       = data?.stats       ?? SKELETON_STATS
  const recentRuns  = data?.recent_runs ?? []
  const schedules   = data?.schedules   ?? []
  const connections = data?.connections ?? []
  const totalToday  = data?.total_today ?? 0

  const submit = () => {
    const text = prompt.trim()
    if (!text || ai.creating) return
    void ai.generate(text, kind)
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[1160px] mx-auto px-[28px] sm:px-[48px] pt-[40px] sm:pt-[56px] pb-[80px] flex flex-col gap-[40px]">
        <GreetingRow />

        <StatsGrid items={stats} />

        <PromptCard
          prompt={prompt}
          onPromptChange={setPrompt}
          onSubmit={submit}
          busy={ai.creating}
          statusMessage={ai.statusMessage}
          kind={kind}
          onKindChange={setKind}
          placeholder={kind === 'crew' ? 'What should this crew do?' : 'What workflow shall we automate?'}
        />

        <SuggestionChips
          suggestions={SUGGESTIONS}
          onPick={setPrompt}
          disabled={ai.creating}
        />

        <div className="grid grid-cols-1 lg:grid-cols-[1.55fr_1fr] gap-[18px] items-start">
          <RecentRuns
            items={recentRuns}
            totalToday={totalToday}
            onViewAll={() => navigate(APP_ROUTES.RUNS)}
          />
          <div className="flex flex-col gap-[14px]">
            <SchedulePanel
              items={schedules}
              onViewAll={() => navigate(APP_ROUTES.SCHEDULES)}
            />
            <ConnectionsPanel
              items={connections}
              totalActive={connections.filter(c => c.state === 'ok').length}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

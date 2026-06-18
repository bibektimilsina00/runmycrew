import {
  Bot, Workflow, Bell, Calendar, Repeat,
  Lightbulb, ShieldAlert, Search as SearchIcon, BookOpen,
} from 'lucide-react'
import { useWorkflowEditorStore } from '../../../../stores/workflowEditorStore'

interface Suggestion {
  title: string
  description: string
  prompt: string
  Icon: React.FC<{ className?: string }>
}

const EMPTY_CANVAS_SUGGESTIONS: Suggestion[] = [
  {
    title: 'Notion → email',
    description: 'When a row is added in Notion, send a welcome email.',
    prompt: 'When a new row is added to Notion, send a welcome email.',
    Icon: Workflow,
  },
  {
    title: 'Watch Slack',
    description: 'Notify me about new messages in a Slack channel.',
    prompt: 'Watch a Slack channel for new messages and notify me.',
    Icon: Bell,
  },
  {
    title: 'Daily digest',
    description: 'Schedule a recurring digest from data I already have.',
    prompt: 'Schedule a daily digest at 9am.',
    Icon: Calendar,
  },
  {
    title: 'Sync APIs',
    description: 'Mirror data from one service to another on a schedule.',
    prompt: 'Sync data from API A to API B every hour.',
    Icon: Repeat,
  },
]

const NON_EMPTY_CANVAS_SUGGESTIONS: Suggestion[] = [
  {
    title: 'Explain this workflow',
    description: 'Summarize what this workflow does, in plain English.',
    prompt: 'Explain what this workflow does, step by step.',
    Icon: BookOpen,
  },
  {
    title: 'Suggest improvements',
    description: 'Propose simplifications, missing checks, or better defaults.',
    prompt: 'Suggest improvements to this workflow.',
    Icon: Lightbulb,
  },
  {
    title: 'Add error handling',
    description: 'Wrap critical nodes with retries and an error branch.',
    prompt: 'Add error handling to the critical nodes in this workflow.',
    Icon: ShieldAlert,
  },
  {
    title: 'Find issues',
    description: 'Scan for missing inputs, dead branches, or unused nodes.',
    prompt: 'Find issues in this workflow.',
    Icon: SearchIcon,
  },
]

interface Props {
  onSend: (text: string) => void
  disabled?: boolean
}

/**
 * Context-aware Copilot empty state.
 *
 * Picks one of two suggestion sets based on whether the editor canvas has
 * any nodes — starter ideas for an empty canvas, or follow-up actions for
 * an existing graph. Clicking a card fires `onSend` immediately, so the
 * card acts as a single-tap shortcut to a useful prompt.
 */
export function CopilotEmptyState({ onSend, disabled }: Props) {
  const hasNodes = useWorkflowEditorStore((s) => s.nodes.length > 0)
  const workflowName = useWorkflowEditorStore((s) => s.workflow?.name)
  const suggestions = hasNodes ? NON_EMPTY_CANVAS_SUGGESTIONS : EMPTY_CANVAS_SUGGESTIONS

  return (
    <div className="flex h-full flex-col items-center justify-center px-4 py-6">
      <div className="mb-4 flex h-[40px] w-[40px] items-center justify-center rounded-[10px] bg-[var(--accent)] text-white">
        <Bot className="h-[20px] w-[20px]" strokeWidth={1.8} />
      </div>
      <h2 className="text-[14px] font-semibold text-[var(--text)]">
        {hasNodes ? `What's next for ${workflowName ?? 'this workflow'}?` : 'Build something with Copilot'}
      </h2>
      <p className="mb-5 mt-1 max-w-xs text-center text-[12px] text-[var(--text-mute)]">
        {hasNodes
          ? 'Pick a quick action below, or describe a change in your own words.'
          : 'Describe what you want to automate. Copilot turns it into a workflow.'}
      </p>

      <div className="grid w-full max-w-md grid-cols-1 gap-2 sm:grid-cols-2">
        {suggestions.map((s) => (
          <button
            key={s.title}
            disabled={disabled}
            onClick={() => onSend(s.prompt)}
            className="group flex flex-col items-start gap-[6px] rounded-[10px] border border-[var(--border-soft)] bg-[rgba(255,255,255,0.02)] p-[12px] text-left transition-colors hover:border-[var(--border)] hover:bg-[rgba(255,255,255,0.05)] disabled:cursor-default disabled:opacity-40"
          >
            <div className="flex items-center gap-[8px]">
              <span className="flex h-[22px] w-[22px] items-center justify-center rounded-[6px] bg-[var(--accent)] text-white">
                <s.Icon className="h-[13px] w-[13px]" />
              </span>
              <span className="text-[12.5px] font-semibold text-[var(--text)]">{s.title}</span>
            </div>
            <p className="text-[11.5px] leading-snug text-[var(--text-faint)]">{s.description}</p>
          </button>
        ))}
      </div>
    </div>
  )
}

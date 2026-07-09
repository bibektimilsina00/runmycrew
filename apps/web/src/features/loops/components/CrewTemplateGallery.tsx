import { useQueryClient } from '@tanstack/react-query'
import { GitBranch, ListChecks, PenLine, Search as SearchIcon, ShieldCheck, Sparkles } from 'lucide-react'
import { useCreateLoop } from '../hooks/useLoops'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'
import { CREW_PRESETS } from '../utils/crewPresets'
import type { StarterGraph } from '../utils/starterCrew'

/**
 * Curated multi-agent starter graphs shown on the Crews landing page.
 *
 * Each template is a pre-wired chain of nodes referenced by CREW_PRESETS.
 * Node types missing from the backend registry silently drop, so the
 * seeded crew never contains a broken node. Clicking a card creates a
 * crew with that graph and drops the user straight into the editor.
 */

const TRIGGER_TYPE = 'trigger.manual'
const COL_GAP = 300
const ROW_Y = 200

interface Template {
  id: string
  name: string
  description: string
  icon: React.FC<{ size?: number }>
  color: string
  chain: string[]
}

const TEMPLATES: Template[] = [
  {
    id: 'research-write',
    name: 'Research → Write → Review',
    description: 'Plan a topic, fan-out research to parallel agents, draft the writeup, then a reviewer signs off.',
    icon: PenLine,
    color: '#f59e0b',
    chain: ['task-planner', 'parallel-agents', 'reviewer'],
  },
  {
    id: 'plan-build-verify',
    name: 'Plan → Build → Verify → Loop',
    description: 'Classic build loop: planner writes a spec, worker implements, verify checks, retries until green.',
    icon: ShieldCheck,
    color: '#10b981',
    chain: ['crew', 'planner', 'worker', 'verify'],
  },
  {
    id: 'parallel-research',
    name: 'Parallel research fan-out',
    description: 'One planner decomposes the goal, N agents research in parallel, a reviewer synthesises.',
    icon: GitBranch,
    color: '#0ea5e9',
    chain: ['task-planner', 'parallel-agents'],
  },
  {
    id: 'q-and-a',
    name: 'Q&A + Human approval',
    description: 'Agent answers, a human approves before anything ships. Great for outbound comms.',
    icon: ListChecks,
    color: '#8b5cf6',
    chain: ['planner', 'human-approval'],
  },
  {
    id: 'crawl-summarize',
    name: 'Crawl + summarize',
    description: 'Worker gathers content, evaluator scores it, memory retains what mattered.',
    icon: SearchIcon,
    color: '#f43f5e',
    chain: ['worker', 'reviewer', 'memory'],
  },
]

function buildGraphForTemplate(template: Template, availableTypes: Set<string>): StarterGraph {
  const nodes: StarterGraph['nodes'] = []
  const edges: StarterGraph['edges'] = []
  const idByKey = new Map<string, string>()

  if (availableTypes.has(TRIGGER_TYPE)) {
    const id = crypto.randomUUID()
    idByKey.set('trigger', id)
    nodes.push({ id, type: TRIGGER_TYPE, position: { x: 0, y: ROW_Y }, data: { label: 'Start', properties: {} } })
  }

  template.chain.forEach((presetId, i) => {
    const preset = CREW_PRESETS.find(p => p.id === presetId)
    if (!preset || !availableTypes.has(preset.nodeType)) return
    const id = crypto.randomUUID()
    idByKey.set(presetId, id)
    nodes.push({
      id,
      type: preset.nodeType,
      position: { x: (i + 1) * COL_GAP, y: ROW_Y },
      data: { label: preset.label, properties: { ...preset.defaultProperties } },
    })
  })

  const chainWithTrigger = idByKey.has('trigger') ? ['trigger', ...template.chain] : template.chain
  for (let i = 0; i < chainWithTrigger.length - 1; i++) {
    const source = idByKey.get(chainWithTrigger[i])
    const target = idByKey.get(chainWithTrigger[i + 1])
    if (source && target) edges.push({ id: crypto.randomUUID(), source, target })
  }

  return { nodes, edges }
}

interface CrewTemplateGalleryProps {
  variant?: 'strip' | 'hero'
}

export function CrewTemplateGallery({ variant = 'strip' }: CrewTemplateGalleryProps) {
  const qc = useQueryClient()
  const createLoop = useCreateLoop()

  const spawn = async (template: Template) => {
    const defs = await qc.ensureQueryData({
      queryKey: ['node-definitions'],
      queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
      staleTime: 1000 * 60 * 10,
    })
    const types = new Set(defs.map(d => d.type))
    const graph = buildGraphForTemplate(template, types)
    createLoop.mutate({ name: template.name, description: template.description, graph })
  }

  const isStrip = variant === 'strip'

  return (
    <section className={isStrip ? 'my-4' : 'mt-2'}>
      <div className="mb-3 flex items-center gap-2">
        <Sparkles size={14} className="text-[var(--text-mute)]" />
        <h2 className="text-[13px] font-semibold text-[var(--text)]">
          {isStrip ? 'Quick-start templates' : 'Start from a template'}
        </h2>
        <span className="text-[11.5px] text-[var(--text-faint)]">
          {isStrip ? 'pre-wired multi-agent flows' : 'each card ships a working crew'}
        </span>
      </div>
      <div
        className={
          isStrip
            ? 'grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-5'
            : 'grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3'
        }
      >
        {TEMPLATES.map(t => (
          <button
            key={t.id}
            onClick={() => spawn(t)}
            disabled={createLoop.isPending}
            className="group flex flex-col gap-2 rounded-[11px] border border-[var(--border-faint)] bg-[var(--bg-2)] p-3 text-left transition-colors hover:border-[var(--border)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            <div className="flex items-center gap-2">
              <span
                className="flex h-8 w-8 items-center justify-center rounded-[8px]"
                style={{ background: `${t.color}22`, color: t.color }}
              >
                <t.icon size={14} />
              </span>
              <span className="truncate text-[13px] font-semibold text-[var(--text)]">{t.name}</span>
            </div>
            <p className="text-[11.5px] leading-relaxed text-[var(--text-mute)] line-clamp-3">
              {t.description}
            </p>
          </button>
        ))}
      </div>
    </section>
  )
}

'use client'

import { useState, type CSSProperties } from 'react'
import {
  Search,
  ChevronsUpDown,
  ChevronDown,
  Plus,
  Plug,
  Home,
  Workflow,
  Users,
  Layers,
  Activity,
  Clock,
  Terminal,
  Check,
  Mic,
  ArrowUp,
  ArrowUpRight,
  HelpCircle,
  MessageSquare,
  ChevronRight,
} from 'lucide-react'
import { BrandMark } from './BrandMark'
import { BrandGlyph } from './BrandGlyph'

/**
 * Hero product shot — a faithful, interactive recreation of the RunMyCrew
 * dashboard (apps/web). It mirrors the real app panel-for-panel and reuses
 * the app's exact design tokens (scoped as CSS variables on the window
 * root), so the class strings match production 1:1.
 *
 * Interactive: workspace nav switches, the Build-with-AI model selector
 * opens a popover, the workflow/crew segmented control toggles, and the
 * suggested-automation cards fill the prompt — enough to feel live without
 * shipping the whole app.
 */

/* Real app palette (apps/web/src/index.css, dark theme). */
const THEME = {
  '--bg': '#1c1c1c',
  '--bg-2': '#1e1e1e',
  '--surface': '#262626',
  '--surface-2': '#303030',
  '--surface-3': '#3b3b3b',
  '--border': 'rgba(255,255,255,0.16)',
  '--border-soft': 'rgba(255,255,255,0.10)',
  '--border-faint': 'rgba(255,255,255,0.06)',
  '--text': '#f3f4f6',
  '--text-body': '#d1d5db',
  '--text-mute': '#9ca3af',
  '--text-faint': '#7a7f8a',
  '--text-dim': '#656973',
  '--accent': '#5e6ad2',
  '--accent-soft': 'rgba(94,106,210,0.14)',
  '--accent-line': 'rgba(94,106,210,0.45)',
  '--ok': '#4cc38a',
  '--warn': '#e7b766',
  '--err': '#e5675f',
  '--badge-ok-bg': 'rgba(76,195,138,0.12)',
} as CSSProperties

const STATS = [
  { label: 'Runs today',       value: '214',  unit: '',   delta: '34%',  dir: 'up' as const, icon: Activity, spark: [4, 6, 5, 8, 7, 9, 8, 11, 10, 13] },
  { label: 'Success rate',     value: '99.2', unit: '%',  delta: '1.1pp', dir: 'up' as const, icon: Check,    spark: [7, 7, 8, 7, 8, 8, 9, 8, 9, 9] },
  { label: 'Time saved',       value: '18',   unit: 'hr', delta: '2.4',  dir: 'up' as const, icon: Clock,    spark: [3, 4, 4, 5, 6, 6, 7, 8, 8, 9] },
  { label: 'Active workflows', value: '22',   unit: '',   delta: '3',    dir: 'up' as const, icon: Layers,   spark: [8, 8, 7, 8, 9, 8, 9, 9, 8, 9] },
]

const SUGGESTIONS = [
  'Every weekday at 9am, summarize new GitHub issues and post to Slack',
  'When a new row is added to Notion, send a welcome email',
  'Fetch JSON from an API and save it to a database',
]

const MODELS = ['Claude Sonnet', 'Claude Opus', 'GPT-5', 'Gemini 2.5 Pro']

const WORKSPACE_NAV = [
  { id: 'home',        label: 'Home',        icon: Home },
  { id: 'automations', label: 'Automations', icon: Workflow, count: '22' },
  { id: 'personas',    label: 'Personas',    icon: Users },
  { id: 'templates',   label: 'Templates',   icon: Layers },
]

const OPERATE_NAV = [
  { id: 'runs',      label: 'Runs',      icon: Activity },
  { id: 'schedules', label: 'Schedules', icon: Clock },
  { id: 'logs',      label: 'Logs',      icon: Terminal },
]

const RUNS = [
  { name: 'Daily standup digest',  trigger: 'Schedule', dur: '1.2s', ago: '9:00', status: 'ok' as const },
  { name: 'Urgent issue → Slack',  trigger: 'Webhook',  dur: '0.4s', ago: '8:41', status: 'ok' as const },
  { name: 'New lead → Notion CRM', trigger: 'Meta',     dur: '0.9s', ago: '8:32', status: 'ok' as const },
  { name: 'Weekly metrics digest', trigger: 'Schedule', dur: '2.1s', ago: '7:00', status: 'warn' as const },
]

const SCHEDULES = [
  { time: '9:00',  name: 'Daily standup digest', sub: '0 9 * * 1-5' },
  { time: '12:00', name: 'Weekly metrics digest', sub: '0 12 * * 5' },
  { time: '17:00', name: 'EOD summary',           sub: '0 17 * * *' },
]

const CONNECTIONS = [
  { name: 'GitHub', provider: 'GitHub',           slug: 'github', bg: '#24292f' },
  { name: 'Slack',  provider: 'Slack',            slug: 'slack',  bg: '#4a154b' },
  { name: 'Google', provider: 'Google Workspace', slug: 'google', bg: '#1a73e8' },
]

const STATUS_TONE = {
  ok:   { dot: 'var(--ok)',   glow: 'rgba(76,195,138,0.18)' },
  warn: { dot: 'var(--warn)', glow: 'rgba(231,183,102,0.20)' },
}

export function DashboardMockup() {
  const [activeNav, setActiveNav] = useState('home')
  const [kind, setKind] = useState<'workflow' | 'crew'>('workflow')
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState(MODELS[0])
  const [modelOpen, setModelOpen] = useState(false)

  return (
    <div className="relative mt-16 pb-[124px] sm:mt-24 sm:pb-[150px]">
      <div
        style={THEME}
        className="relative z-10 flex h-[1200px] overflow-hidden rounded-[14px] border border-[var(--border)] bg-[var(--bg)] text-[var(--text)] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]"
      >
        {/* Top-edge sheen — the highlight real windows catch. */}
        <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 z-20 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent" />

        <Sidebar activeNav={activeNav} setActiveNav={setActiveNav} />

        {/* ── Main column ─────────────────────────────────────── */}
        <div className="flex min-w-0 flex-1 flex-col bg-[var(--bg)]">
          <Topbar />

          <div className="flex-1 overflow-hidden">
            <div className="mx-auto flex h-full max-w-[1160px] flex-col gap-[26px] overflow-hidden px-[30px] pb-[30px] pt-[26px]">
              <GreetingRow />
              <StatsGrid />
              <PromptCard
                prompt={prompt}
                setPrompt={setPrompt}
                kind={kind}
                setKind={setKind}
                model={model}
                setModel={setModel}
                modelOpen={modelOpen}
                setModelOpen={setModelOpen}
              />
              <Suggestions onPick={setPrompt} />
              <div className="grid grid-cols-1 items-start gap-[18px] lg:grid-cols-[1.55fr_1fr]">
                <RecentRuns />
                <div className="flex flex-col gap-[14px]">
                  <SchedulePanel />
                  <ConnectionsPanel />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Lit-floor environment — Linear's exact technique: a full-bleed div
          behind the window with a dark→light-grey vertical gradient (the
          floor) plus a radial vignette darkening the corners. The opaque
          window hides the middle; the light shows below it and in the lower
          gutters. Sized like Linear's wrapper (window top → base + 28px). */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-0 z-0 h-[1320px] w-screen -translate-x-1/2 select-none"
        style={{
          background:
            'radial-gradient(52.53% 57.5% at 50% 100%, rgba(8,9,10,0) 0%, rgba(8,9,10,0.5) 100%), linear-gradient(#08090a 10%, #d0d6e0 100%)',
        }}
      />
    </div>
  )
}

/* ─── Sidebar ───────────────────────────────────────────────────────── */

function Sidebar({ activeNav, setActiveNav }: { activeNav: string; setActiveNav: (id: string) => void }) {
  return (
    <aside className="hidden w-[236px] shrink-0 flex-col border-r border-[var(--border-faint)] bg-[var(--bg-2)] md:flex">
      {/* Header: logo + collapse */}
      <div className="flex flex-col gap-[10px] border-b border-[var(--border-faint)] px-[12px] pb-[10px] pt-[14px]">
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-[9px] text-[15px] font-semibold tracking-[-0.02em] text-[var(--text)]">
            <BrandMark className="h-[22px] w-[22px] text-[var(--accent)]" />
            RunMyCrew
          </span>
          <ChevronsUpDown className="h-[13px] w-[13px] text-[var(--text-faint)]" />
        </div>

        {/* Workspace selector */}
        <button className="mt-[4px] flex items-center gap-[8px] rounded-[8px] border border-[var(--border-faint)] bg-[var(--bg)] px-[9px] py-[6px] transition-colors hover:border-[var(--border-soft)]">
          <span className="grid h-[20px] w-[20px] place-items-center rounded-[6px] bg-[linear-gradient(135deg,var(--surface-3),var(--surface-2))] text-[11px] font-semibold text-white">
            B
          </span>
          <span className="flex-1 text-left text-[13px] font-medium text-[var(--text)]">Bibek&apos;s Workspace</span>
          <ChevronsUpDown className="h-[13px] w-[13px] text-[var(--text-faint)]" />
        </button>

        {/* Search */}
        <div className="flex h-[32px] items-center gap-[8px] rounded-[8px] border border-[var(--border-faint)] bg-[var(--bg)] px-[10px]">
          <Search className="h-[13px] w-[13px] text-[var(--text-faint)]" />
          <span className="flex-1 text-[12.5px] text-[var(--text-dim)]">Search</span>
          <span className="rounded bg-[rgba(255,255,255,0.05)] px-[5px] py-[1px] font-mono text-[10.5px] text-[var(--text-faint)]">⌘K</span>
        </div>
      </div>

      {/* Nav */}
      <div className="flex flex-1 flex-col overflow-hidden px-[8px] pt-[6px]">
        <NavGroup label="Workspace">
          {WORKSPACE_NAV.map((item) => (
            <NavItem key={item.id} item={item} active={activeNav === item.id} onClick={() => setActiveNav(item.id)} />
          ))}
        </NavGroup>

        <NavGroup label="Workflows" count="3" className="mt-[4px] border-t border-[var(--border-faint)] pt-[8px]">
          <WorkflowRow name="Urgent issues → Slack" dot="var(--accent)" active={activeNav === 'wf-1'} onClick={() => setActiveNav('wf-1')} />
          <WorkflowRow name="Weekly digest" dot="var(--ok)" active={activeNav === 'wf-2'} onClick={() => setActiveNav('wf-2')} />
          <WorkflowRow name="Lead router" dot="var(--warn)" active={activeNav === 'wf-3'} onClick={() => setActiveNav('wf-3')} />
        </NavGroup>

        <NavGroup label="Operate" className="mt-[4px] border-t border-[var(--border-faint)] pt-[8px]">
          {OPERATE_NAV.map((item) => (
            <NavItem key={item.id} item={item} active={activeNav === item.id} onClick={() => setActiveNav(item.id)} />
          ))}
        </NavGroup>
      </div>

      {/* Footer */}
      <div className="flex h-[36px] shrink-0 items-center gap-1 border-t border-[var(--border-faint)] px-[6px]">
        <button className="inline-flex h-[24px] flex-1 items-center justify-center gap-1 rounded-[7px] px-1 text-[11px] font-medium text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]">
          <HelpCircle className="h-[13px] w-[13px]" /> Help &amp; docs
        </button>
        <button className="inline-flex h-[24px] flex-1 items-center justify-center gap-1 rounded-[7px] px-1 text-[11px] font-medium text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]">
          <MessageSquare className="h-[13px] w-[13px]" /> Feedback
        </button>
      </div>
    </aside>
  )
}

function NavGroup({ label, count, className, children }: { label: string; count?: string; className?: string; children: React.ReactNode }) {
  return (
    <div className={`flex flex-col ${className ?? ''}`}>
      <div className="flex items-center gap-[6px] px-[10px] pb-[5px] pt-[10px]">
        <span className="flex-1 text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[var(--text-dim)]">{label}</span>
        {count && <span className="font-mono text-[10.5px] font-medium text-[var(--text-faint)]">{count}</span>}
      </div>
      <div className="flex flex-col gap-[2px] pl-[6px]">{children}</div>
    </div>
  )
}

function NavItem({ item, active, onClick }: { item: { label: string; icon: typeof Home; count?: string }; active: boolean; onClick: () => void }) {
  const Icon = item.icon
  return (
    <button
      onClick={onClick}
      className={`relative flex w-full items-center gap-[10px] rounded-[8px] px-[10px] py-[6px] text-left text-[13px] font-medium transition-colors ${
        active
          ? 'bg-[var(--surface)] text-[var(--text)] before:absolute before:left-0 before:h-[14px] before:w-[3px] before:rounded-[0_2px_2px_0] before:bg-[var(--text)] before:content-[""]'
          : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]'
      }`}
    >
      <Icon className="h-[15px] w-[15px] opacity-85" strokeWidth={1.9} />
      <span className="flex-1">{item.label}</span>
      {item.count && <span className="font-mono text-[10.5px] font-medium text-[var(--text-faint)]">{item.count}</span>}
    </button>
  )
}

function WorkflowRow({ name, dot, active, onClick }: { name: string; dot: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-center gap-[9px] rounded-[8px] px-[10px] py-[6px] text-left text-[13px] font-medium transition-colors ${
        active ? 'bg-[var(--surface)] text-[var(--text)]' : 'text-[var(--text-mute)] hover:bg-[var(--surface)] hover:text-[var(--text)]'
      }`}
    >
      <span className="h-[7px] w-[7px] shrink-0 rounded-full" style={{ background: dot }} />
      <span className="flex-1 truncate">{name}</span>
    </button>
  )
}

/* ─── Topbar ────────────────────────────────────────────────────────── */

function Topbar() {
  return (
    <header className="flex shrink-0 items-center justify-between border-b border-[var(--border-faint)] bg-[var(--bg-2)] px-[22px] py-[8px]">
      <div className="flex items-center gap-[8px] text-[13px] text-[var(--text-mute)]">
        <span>Bibek&apos;s Workspace</span>
        <span className="text-[var(--text-dim)]">/</span>
        <span className="font-medium text-[var(--text)]">Home</span>
      </div>
      <span className="grid h-[26px] w-[26px] place-items-center rounded-full bg-[linear-gradient(135deg,var(--surface-3),var(--surface-2))] text-[11px] font-semibold text-white">
        B
      </span>
    </header>
  )
}

/* ─── Greeting ──────────────────────────────────────────────────────── */

function GreetingRow() {
  const date = 'WED, JUN 18'
  return (
    <div className="flex flex-col gap-[16px]">
      <div className="flex items-center gap-[8px]">
        <span className="inline-flex h-[8px] w-[8px]">
          <span className="h-full w-full animate-[rmcPulse_2.4s_ease-in-out_infinite] rounded-full bg-[var(--ok)]" />
        </span>
        <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-faint)]">ALL SYSTEMS OPERATIONAL</span>
        <span className="text-[var(--text-dim)]">·</span>
        <span className="text-[11px] font-semibold tracking-[0.08em] text-[var(--text-dim)]">{date}</span>
      </div>
      <div className="flex flex-wrap items-end justify-between gap-[16px]">
        <h1 className="m-0 min-w-[280px] flex-1 text-[27px] font-semibold tracking-[-0.022em] text-[var(--text)]">Good evening, Bibek</h1>
        <div className="flex shrink-0 items-center gap-[9px]">
          <button className="inline-flex items-center gap-[7px] rounded-[6px] border border-[var(--border-soft)] bg-[rgba(255,255,255,0.02)] px-[14px] py-[8px] text-[13px] font-medium text-[var(--text)] transition-colors hover:border-[var(--border)] hover:bg-[rgba(255,255,255,0.05)]">
            <Plug className="h-[15px] w-[15px]" strokeWidth={1.9} /> Connect app
          </button>
          <button className="inline-flex items-center gap-[7px] rounded-[6px] bg-[var(--accent)] px-[14px] py-[8px] text-[13px] font-semibold text-white transition-[filter] hover:brightness-110">
            <Plus className="h-[15px] w-[15px]" strokeWidth={2.2} /> New automation
          </button>
        </div>
      </div>
    </div>
  )
}

/* ─── Stats ─────────────────────────────────────────────────────────── */

function StatsGrid() {
  return (
    <div className="grid grid-cols-4 gap-[16px]">
      {STATS.map((s) => {
        const Icon = s.icon
        return (
          <div key={s.label} className="flex flex-col rounded-[10px] border border-[var(--border-faint)] bg-[var(--surface)] px-[16px] py-[14px]">
            <div className="flex items-start justify-between">
              <div className="inline-flex items-center gap-[8px] text-[var(--text-mute)]">
                <Icon className="h-[15px] w-[15px]" strokeWidth={1.9} />
                <span className="text-[11.5px] font-medium">{s.label}</span>
              </div>
              <Spark data={s.spark} />
            </div>
            <div className="mt-[9px] flex items-baseline gap-[3px]">
              <span className="font-mono text-[24px] font-semibold tracking-[-0.02em] text-[var(--text)]">{s.value}</span>
              {s.unit && <span className="text-[13px] font-medium text-[var(--text-faint)]">{s.unit}</span>}
            </div>
            <div className="mt-[6px] inline-flex items-center gap-[5px] text-[11.5px] font-semibold text-[var(--ok)]">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="6 11 12 5 18 11" />
              </svg>
              <span>{s.delta}</span>
              <span className="font-medium text-[var(--text-dim)]">vs yesterday</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function Spark({ data }: { data: number[] }) {
  const w = 58, h = 19
  const max = Math.max(...data), min = Math.min(...data), range = max - min || 1
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * (h - 4) - 2}`).join(' ')
  const lastY = h - ((data[data.length - 1] - min) / range) * (h - 4) - 2
  return (
    <svg viewBox={`0 0 ${w} ${h}`} fill="none" className="h-[19px] w-[58px]">
      <polyline points={pts} stroke="var(--ok)" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
      <circle cx={w} cy={lastY} r="1.8" fill="var(--ok)" />
    </svg>
  )
}

/* ─── Prompt card ───────────────────────────────────────────────────── */

function PromptCard({
  prompt, setPrompt, kind, setKind, model, setModel, modelOpen, setModelOpen,
}: {
  prompt: string
  setPrompt: (v: string) => void
  kind: 'workflow' | 'crew'
  setKind: (k: 'workflow' | 'crew') => void
  model: string
  setModel: (m: string) => void
  modelOpen: boolean
  setModelOpen: (v: boolean) => void
}) {
  const placeholder = kind === 'crew' ? 'What should this crew do?' : 'What workflow shall we automate?'
  return (
    <div className="overflow-visible rounded-[12px] border border-[var(--border-soft)] bg-[var(--surface)]">
      {/* Header */}
      <div className="relative flex items-center gap-[9px] px-[20px] py-[14px]">
        <span className="inline-flex h-[26px] w-[26px] shrink-0 items-center justify-center text-[var(--accent)]">
          <BrandMark className="h-[22px] w-[22px]" />
        </span>
        <span className="text-[13.5px] font-semibold text-[var(--text)]">Build with AI</span>
        <button
          onClick={() => setModelOpen(!modelOpen)}
          className="ml-auto inline-flex items-center gap-[6px] rounded-[7px] border border-[var(--border-soft)] px-[9px] py-[4px] text-[12px] font-medium text-[var(--text-mute)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
        >
          <span className="h-[6px] w-[6px] rounded-full bg-[var(--ok)]" />
          {model}
          <ChevronDown className={`h-[12px] w-[12px] transition-transform ${modelOpen ? 'rotate-180' : ''}`} />
        </button>
        {modelOpen && (
          <>
            <div className="fixed inset-0 z-30" onClick={() => setModelOpen(false)} />
            <div className="absolute right-[20px] top-[46px] z-40 w-[176px] rounded-[10px] border border-[var(--border)] bg-[var(--bg-2)] p-[5px] shadow-[0_24px_56px_-20px_rgba(0,0,0,0.7)]">
              {MODELS.map((m) => (
                <button
                  key={m}
                  onClick={() => { setModel(m); setModelOpen(false) }}
                  className="flex w-full items-center gap-[8px] rounded-[7px] px-[10px] py-[7px] text-left text-[13px] font-medium text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
                >
                  <span className={`h-[6px] w-[6px] rounded-full ${m === model ? 'bg-[var(--ok)]' : 'bg-[var(--text-dim)]'}`} />
                  <span className="flex-1">{m}</span>
                  {m === model && <Check className="h-[13px] w-[13px] text-[var(--accent)]" />}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Body */}
      <div className="px-[20px] pb-[14px] pt-[4px]">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={2}
          placeholder={placeholder}
          className="block min-h-[50px] w-full resize-none border-none bg-transparent text-[15px] leading-[1.55] tracking-[-0.005em] text-[var(--text)] outline-none placeholder:text-[var(--text-dim)]"
        />
        <div className="mt-[14px] flex items-center justify-between gap-2">
          {/* workflow / crew toggle */}
          <div className="inline-flex items-center rounded-[8px] border border-[var(--border-soft)] bg-[var(--surface-2)] p-[2px]">
            {(['workflow', 'crew'] as const).map((k) => (
              <button
                key={k}
                onClick={() => setKind(k)}
                className={`inline-flex items-center gap-[5px] rounded-[6px] px-[9px] py-[4px] text-[12px] font-medium capitalize transition-colors ${
                  kind === k
                    ? 'bg-[var(--surface)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-soft)]'
                    : 'text-[var(--text-mute)] hover:text-[var(--text)]'
                }`}
              >
                {k === 'workflow' ? <Workflow className="h-[13px] w-[13px]" /> : <Users className="h-[13px] w-[13px]" />}
                {k}
              </button>
            ))}
          </div>
          <div className="ml-auto flex items-center gap-[10px]">
            <span className="hidden items-center gap-[5px] text-[11.5px] text-[var(--text-dim)] sm:inline-flex">
              <kbd className="rounded border border-[var(--border-soft)] bg-[var(--surface-2)] px-[5px] py-[1px] font-mono text-[10.5px]">↵</kbd> to send
            </span>
            <button className="inline-flex h-[34px] w-[34px] items-center justify-center rounded-[9px] border border-[var(--border-soft)] text-[var(--text-mute)] transition-colors hover:bg-[rgba(255,255,255,0.06)] hover:text-[var(--text)]">
              <Mic className="h-[15px] w-[15px]" />
            </button>
            <button
              disabled={!prompt.trim()}
              className="inline-flex h-[34px] w-[34px] items-center justify-center rounded-[9px] bg-[var(--accent)] text-white shadow-[0_4px_14px_var(--accent-soft)] transition-[filter] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-30"
            >
              <ArrowUp className="h-[16px] w-[16px]" strokeWidth={2.2} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ─── Suggestions ───────────────────────────────────────────────────── */

function Suggestions({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex flex-col gap-[12px]">
      <div className="mx-[2px] flex items-center gap-[8px]">
        <span className="text-[11px] font-semibold tracking-[0.07em] text-[var(--text-faint)]">SUGGESTED AUTOMATIONS</span>
        <span className="h-px flex-1 bg-[var(--border-faint)]" />
      </div>
      <div className="grid grid-cols-3 gap-[12px]">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="group flex flex-col gap-[11px] rounded-[11px] border border-[var(--border-soft)] bg-[rgba(255,255,255,0.015)] px-[16px] py-[15px] text-left transition-colors hover:border-[var(--border)] hover:bg-[rgba(255,255,255,0.045)]"
          >
            <span className="flex items-center justify-end">
              <ArrowUpRight className="h-[15px] w-[15px] text-[var(--text-dim)] transition-colors group-hover:text-[var(--text-mute)]" strokeWidth={1.9} />
            </span>
            <span className="text-[13.5px] font-medium leading-[1.4] text-[var(--text)]">{s}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

/* ─── Bottom panels: recent runs, schedule, connections ─────────────── */

function PanelHead({
  icon, title, count, countTone, action,
}: {
  icon: React.ReactNode
  title: string
  count?: string
  countTone?: 'ok' | 'neutral'
  action: string
}) {
  return (
    <div className="flex items-center gap-[9px] px-[15px] pb-[10px] pt-[14px]">
      <span className="inline-flex items-center justify-center text-[var(--text-mute)]">{icon}</span>
      <span className="text-[13.5px] font-semibold text-[var(--text)]">{title}</span>
      {count && (
        <span
          className={
            countTone === 'ok'
              ? 'rounded-[5px] bg-[var(--badge-ok-bg)] px-[7px] py-[2px] text-[11px] font-semibold text-[var(--ok)]'
              : 'rounded-[5px] bg-[rgba(255,255,255,0.05)] px-[7px] py-[2px] font-mono text-[11px] font-medium text-[var(--text-mute)]'
          }
        >
          {count}
        </span>
      )}
      <button className="ml-auto inline-flex items-center gap-[4px] rounded-[6px] px-[8px] py-[4px] text-[12px] font-medium text-[var(--text-faint)] transition-colors hover:bg-[rgba(255,255,255,0.05)] hover:text-[var(--text)]">
        {action}
        <ChevronRight className="h-[13px] w-[13px]" />
      </button>
    </div>
  )
}

function RecentRuns() {
  return (
    <div className="flex flex-col overflow-hidden rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]">
      <PanelHead icon={<Activity className="h-[15px] w-[15px]" strokeWidth={1.9} />} title="Recent runs" count="214 today" action="View all" />
      <div className="flex flex-col gap-[2px] px-[8px] pb-[8px]">
        {RUNS.map((r) => {
          const tone = STATUS_TONE[r.status]
          return (
            <button key={r.name} className="flex w-full items-center gap-[12px] rounded-[6px] px-[12px] py-[8px] text-left transition-colors hover:bg-[rgba(255,255,255,0.04)]">
              <span className="h-[8px] w-[8px] shrink-0 rounded-full" style={{ background: tone.dot, boxShadow: `0 0 0 3px ${tone.glow}` }} />
              <span className="min-w-0 flex-1 truncate text-[13px] font-medium text-[var(--text)]">{r.name}</span>
              <span className="rounded-[5px] border border-[var(--border-soft)] bg-[rgba(255,255,255,0.04)] px-[7px] py-[2px] font-mono text-[11.5px] text-[var(--text-mute)]">{r.trigger}</span>
              <span className="w-[54px] text-right font-mono text-[11.5px] text-[var(--text-faint)]">{r.dur}</span>
              <span className="w-[40px] text-right text-[11.5px] text-[var(--text-dim)]">{r.ago}</span>
              <ChevronRight className="h-[14px] w-[14px] shrink-0 text-[var(--text-dim)]" />
            </button>
          )
        })}
      </div>
    </div>
  )
}

function SchedulePanel() {
  return (
    <div className="flex flex-col overflow-hidden rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]">
      <PanelHead icon={<Clock className="h-[15px] w-[15px]" strokeWidth={1.9} />} title="Next 12 hours" action="All" />
      <div className="flex flex-col gap-[2px] px-[8px] pb-[8px]">
        {SCHEDULES.map((s) => (
          <button key={s.name} className="flex w-full items-center gap-[12px] rounded-[6px] px-[12px] py-[8px] text-left transition-colors hover:bg-[rgba(255,255,255,0.04)]">
            <span className="w-[46px] shrink-0 font-mono text-[11.5px] text-[var(--text)]">{s.time}</span>
            <span className="flex min-w-0 flex-1 flex-col gap-[2px]">
              <span className="truncate text-[12.5px] font-medium text-[var(--text)]">{s.name}</span>
              <span className="truncate font-mono text-[11px] text-[var(--text-faint)]">{s.sub}</span>
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

function ConnectionsPanel() {
  return (
    <div className="flex flex-col overflow-hidden rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]">
      <PanelHead icon={<Plug className="h-[15px] w-[15px]" strokeWidth={1.9} />} title="Connections" count="3 active" countTone="ok" action="Manage" />
      <div className="flex flex-col gap-[2px] px-[8px] pb-[8px]">
        {CONNECTIONS.map((c) => (
          <button key={c.name} className="flex w-full items-center gap-[11px] rounded-[6px] px-[12px] py-[8px] text-left transition-colors hover:bg-[rgba(255,255,255,0.04)]">
            <span className="grid h-[30px] w-[30px] shrink-0 place-items-center rounded-[8px]" style={{ background: c.bg }}>
              <BrandGlyph slug={c.slug} size={16} />
            </span>
            <span className="flex min-w-0 flex-1 flex-col gap-[2px] leading-[1.3]">
              <span className="truncate text-[13px] font-medium text-[var(--text)]">{c.name}</span>
              <span className="truncate text-[11px] text-[var(--text-faint)]">{c.provider}</span>
            </span>
            <span className="inline-flex items-center gap-[5px] rounded-[6px] px-[8px] py-[3px] text-[11px] font-semibold" style={{ background: 'var(--badge-ok-bg)', color: 'var(--ok)' }}>
              <span className="h-[5px] w-[5px] rounded-full" style={{ background: 'var(--ok)' }} />
              OK
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

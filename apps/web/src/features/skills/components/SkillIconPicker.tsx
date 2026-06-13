import { createElement, useMemo, useState } from 'react'
import * as LucideIcons from 'lucide-react'
import { Check, ChevronDown, Search } from 'lucide-react'
import { cn } from '@/lib/cn'

/**
 * Curated icon catalog grouped by purpose. ~50 icons total — broad enough
 * to cover the common skill themes (writing, support, research, data,
 * coding, comms, learning, etc.) without the analysis-paralysis of the
 * full 1500-icon Lucide library.
 */
const ICON_GROUPS: { label: string; icons: string[] }[] = [
  {
    label: 'Knowledge',
    icons: ['BookOpen', 'Book', 'Library', 'GraduationCap', 'NotebookPen', 'StickyNote', 'FileText', 'ScrollText'],
  },
  {
    label: 'Communication',
    icons: ['MessageSquare', 'MessageCircle', 'Mail', 'Send', 'Megaphone', 'Phone', 'Users'],
  },
  {
    label: 'Tools',
    icons: ['Wrench', 'Hammer', 'Settings', 'Cog', 'Sliders', 'Terminal', 'Code2', 'Bug'],
  },
  {
    label: 'Data',
    icons: ['Database', 'BarChart3', 'LineChart', 'PieChart', 'TrendingUp', 'Table', 'Filter', 'Search'],
  },
  {
    label: 'Tasks',
    icons: ['ListTodo', 'CheckSquare', 'Target', 'Flag', 'Clock', 'Calendar', 'AlarmClock'],
  },
  {
    label: 'AI',
    icons: ['Sparkles', 'Bot', 'Brain', 'Lightbulb', 'Wand2', 'Zap'],
  },
]

const ALL_ICONS = ICON_GROUPS.flatMap(g => g.icons)

function resolveIcon(name: string): LucideIcons.LucideIcon | null {
  const icons = LucideIcons as unknown as Record<string, LucideIcons.LucideIcon>
  return icons[name] ?? null
}

interface SkillIconPickerProps {
  value: string
  onChange: (iconName: string) => void
}

export function SkillIconPicker({ value, onChange }: SkillIconPickerProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')

  const filteredGroups = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return ICON_GROUPS
    return ICON_GROUPS.map(group => ({
      ...group,
      icons: group.icons.filter(name => name.toLowerCase().includes(q)),
    })).filter(group => group.icons.length > 0)
  }, [query])

  const Selected = resolveIcon(value) ?? resolveIcon('BookOpen')!

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex h-9 items-center gap-2 rounded-[8px] border border-border-faint bg-bg px-3 transition-colors hover:border-border-soft"
      >
        <span className="flex h-6 w-6 items-center justify-center rounded-[6px] bg-surface text-text-mute">
          {createElement(Selected, { size: 14 })}
        </span>
        <span className="font-mono text-[12px] text-text-mute">{value}</span>
        <ChevronDown size={13} className={cn('text-text-faint transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <>
          <button
            type="button"
            aria-label="Close icon picker"
            className="fixed inset-0 z-20"
            onClick={() => setOpen(false)}
          />
          <div className="absolute left-0 top-11 z-30 w-[320px] overflow-hidden rounded-[10px] border border-border-faint bg-bg-2 shadow-[0_12px_32px_-8px_oklch(0_0_0/0.55)]">
            <div className="flex items-center gap-2 border-b border-border-faint px-3 py-2">
              <Search size={13} className="text-text-faint" />
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Filter icons…"
                autoFocus
                className="flex-1 bg-transparent text-[12.5px] text-text outline-none placeholder:text-text-faint"
              />
            </div>
            <div className="max-h-[300px] overflow-y-auto px-2 py-2">
              {filteredGroups.length === 0 ? (
                <p className="px-2 py-4 text-center text-[11.5px] text-text-faint">
                  No icons match &ldquo;{query}&rdquo;.
                </p>
              ) : (
                filteredGroups.map(group => (
                  <div key={group.label} className="flex flex-col gap-1.5 px-1 pb-2 pt-1">
                    <span className="px-1 text-[9.5px] font-semibold uppercase tracking-wider text-text-faint">
                      {group.label}
                    </span>
                    <div className="grid grid-cols-6 gap-1">
                      {group.icons.map(name => {
                        const Icon = resolveIcon(name)
                        if (!Icon) return null
                        const active = value === name
                        return (
                          <button
                            key={name}
                            type="button"
                            onClick={() => {
                              onChange(name)
                              setOpen(false)
                            }}
                            title={name}
                            className={cn(
                              'relative flex h-8 w-8 items-center justify-center rounded-[6px] transition-colors',
                              active ? 'bg-surface text-text' : 'text-text-mute hover:bg-surface hover:text-text',
                            )}
                          >
                            {createElement(Icon, { size: 15 })}
                            {active && (
                              <Check size={9} className="absolute -right-0.5 -top-0.5 rounded-full bg-accent p-[1px] text-bg" />
                            )}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export { ALL_ICONS as CURATED_SKILL_ICONS }

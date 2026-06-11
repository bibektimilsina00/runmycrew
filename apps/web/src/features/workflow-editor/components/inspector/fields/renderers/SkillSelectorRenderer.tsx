import { useQuery } from '@tanstack/react-query'
import { Check, Loader2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import type { RendererProps } from '../types'

interface Skill {
  id: string
  name: string
  description: string
}

function toIdArray(value: unknown): string[] {
  if (!value) return []
  if (Array.isArray(value)) return value.map(String)
  if (typeof value === 'string') { try { return JSON.parse(value) } catch { return [] } }
  return []
}

export function SkillSelectorRenderer({ value, onChange }: RendererProps) {
  const selected = toIdArray(value)

  const { data: skills = [], isLoading } = useQuery({
    queryKey: ['skills-list'],
    queryFn: async (): Promise<Skill[]> => {
      const res = await apiClient.get('/skills/')
      return Array.isArray(res.data) ? res.data : (res.data?.items ?? [])
    },
    staleTime: 1000 * 60,
  })

  const toggle = (id: string) => {
    const next = selected.includes(id) ? selected.filter(s => s !== id) : [...selected, id]
    onChange(next)
  }

  if (isLoading) {
    return (
      <div className="flex h-8 items-center gap-2 text-[12px] text-text-faint">
        <Loader2 size={13} className="animate-spin" /> Loading skills…
      </div>
    )
  }

  if (skills.length === 0) {
    return <p className="text-[12px] text-text-faint">No skills available. Create skills in the Skills section.</p>
  }

  return (
    <div className="flex flex-col gap-1">
      {skills.map(skill => {
        const active = selected.includes(skill.id)
        return (
          <button
            key={skill.id}
            type="button"
            onClick={() => toggle(skill.id)}
            className={cn(
              'flex items-center gap-2 rounded-[7px] border px-2.5 py-1.5 text-left transition-colors',
              active ? 'border-[var(--accent-line)]/40 bg-[var(--accent-line)]/10' : 'border-border-faint bg-bg hover:bg-surface',
            )}
          >
            <div className={cn(
              'flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] border transition-colors',
              active ? 'border-[var(--accent)] bg-[var(--accent)] text-bg' : 'border-border-faint',
            )}>
              {active && <Check size={10} />}
            </div>
            <span className="flex-1 min-w-0">
              <span className="block text-[12px] font-medium text-text-mute">{skill.name}</span>
              {skill.description && <span className="block text-[10px] text-text-faint">{skill.description}</span>}
            </span>
          </button>
        )
      })}
    </div>
  )
}

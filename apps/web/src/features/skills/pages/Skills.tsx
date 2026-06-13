import { useMemo, useState } from 'react'
import { Plus, Search, Sparkles } from 'lucide-react'
import { Button } from '@/shared/components'
import { useSkills } from '../hooks/useSkills'
import { SkillCard } from '../components/SkillCard'
import { SkillCreateModal } from '../components/SkillCreateModal'
import { SkillDeleteConfirmModal } from '../components/SkillDeleteConfirmModal'
import type { SkillMeta } from '../types/skillTypes'

export function Skills() {
  const { data: skills = [], isLoading } = useSkills()
  const [query, setQuery] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [pendingDelete, setPendingDelete] = useState<SkillMeta | null>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return skills
    return skills.filter(s =>
      s.name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q),
    )
  }, [skills, query])

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border-faint bg-bg-2 px-8 py-6">
        <div className="mx-auto flex max-w-6xl items-end justify-between gap-6">
          <div>
            <h1 className="text-[22px] font-semibold tracking-tight text-text">Skills</h1>
            <p className="mt-1 text-[13px] text-text-mute">
              Reusable instruction bodies the AI agent can load on demand.
            </p>
          </div>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={14} />
            New skill
          </Button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mx-auto flex max-w-6xl flex-col gap-5">
          {/* Search */}
          {skills.length > 0 && (
            <div className="flex h-9 items-center gap-2 rounded-[8px] border border-border-faint bg-bg px-3">
              <Search size={14} className="shrink-0 text-text-faint" />
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Filter by name or description…"
                className="flex-1 bg-transparent text-[13px] text-text outline-none placeholder:text-text-faint"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery('')}
                  className="text-[11px] text-text-faint hover:text-text"
                >
                  Clear
                </button>
              )}
            </div>
          )}

          {/* Grid */}
          {isLoading ? (
            <p className="text-[12.5px] text-text-faint">Loading…</p>
          ) : skills.length === 0 ? (
            <EmptyState onCreate={() => setCreateOpen(true)} />
          ) : filtered.length === 0 ? (
            <p className="rounded-[8px] border border-dashed border-border-faint bg-bg p-8 text-center text-[12.5px] text-text-faint">
              No skills match &ldquo;{query}&rdquo;.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map(skill => (
                <SkillCard key={skill.id} skill={skill} onDelete={setPendingDelete} />
              ))}
            </div>
          )}
        </div>
      </div>

      <SkillCreateModal open={createOpen} onClose={() => setCreateOpen(false)} />
      <SkillDeleteConfirmModal
        skill={pendingDelete}
        onClose={() => setPendingDelete(null)}
      />
    </div>
  )
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-[12px] border border-dashed border-border-faint bg-bg p-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-[10px] bg-accent/10 text-accent">
        <Sparkles size={20} />
      </div>
      <h2 className="text-[15px] font-semibold text-text">No skills yet</h2>
      <p className="max-w-sm text-[12.5px] text-text-mute">
        Skills are reusable instruction bodies an agent can pull in on demand —
        like a playbook for a specific task. The agent only loads them when
        relevant, so they don't bloat every prompt.
      </p>
      <Button onClick={onCreate}>
        <Plus size={14} />
        Create your first skill
      </Button>
    </div>
  )
}

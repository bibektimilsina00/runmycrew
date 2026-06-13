import { useState } from 'react'
import { MoreVertical, Trash2, Pencil } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { APP_ROUTES } from '@/shared/constants/routes'
import { SkillIconBadge } from './SkillIconBadge'
import type { SkillMeta } from '../types/skillTypes'

interface SkillCardProps {
  skill: SkillMeta
  onDelete: (skill: SkillMeta) => void
}

export function SkillCard({ skill, onDelete }: SkillCardProps) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div
      className={cn(
        'group relative flex flex-col gap-3 rounded-[12px] border border-border-faint bg-bg p-4',
        'transition-colors hover:border-border-soft hover:bg-surface',
      )}
    >
      <Link
        to={APP_ROUTES.SKILL_EDIT(skill.id)}
        className="absolute inset-0 rounded-[12px]"
        aria-label={`Edit ${skill.name}`}
      />

      <div className="relative flex items-start gap-3">
        <SkillIconBadge iconName={skill.icon} />
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-[14px] font-semibold text-text">{skill.name}</h3>
          <p className="line-clamp-2 text-[11.5px] leading-snug text-text-mute">
            {skill.description || <em className="text-text-faint">No description</em>}
          </p>
        </div>

        <div className="relative z-10">
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              setMenuOpen(v => !v)
            }}
            className="flex h-7 w-7 items-center justify-center rounded-[6px] text-text-faint opacity-0 transition-opacity hover:bg-bg-2 hover:text-text group-hover:opacity-100"
            aria-label="Open card menu"
          >
            <MoreVertical size={14} />
          </button>
          {menuOpen && (
            <>
              <button
                type="button"
                aria-label="Close menu"
                className="fixed inset-0 z-20"
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  setMenuOpen(false)
                }}
              />
              <div className="absolute right-0 top-8 z-30 w-[140px] overflow-hidden rounded-[8px] border border-border-faint bg-bg-2 shadow-[0_8px_24px_-8px_oklch(0_0_0/0.4)]">
                <Link
                  to={APP_ROUTES.SKILL_EDIT(skill.id)}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-[12px] text-text hover:bg-surface"
                  onClick={() => setMenuOpen(false)}
                >
                  <Pencil size={12} />
                  Edit
                </Link>
                <button
                  type="button"
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-[12px] text-err hover:bg-surface"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    setMenuOpen(false)
                    onDelete(skill)
                  }}
                >
                  <Trash2 size={12} />
                  Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="relative mt-auto flex items-center justify-between text-[10.5px] text-text-faint">
        <span>
          Updated{' '}
          {new Date(skill.updated_at).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
          })}
        </span>
      </div>
    </div>
  )
}

import * as LucideIcons from 'lucide-react'
import { Bot, Copy, Pencil, Trash2 } from 'lucide-react'
import type { Persona } from '../types/personaTypes'

interface PersonaCardProps {
  persona: Persona
  onEdit: (p: Persona) => void
  onDelete: (p: Persona) => void
  onDuplicate: (p: Persona) => void
}

export function PersonaCard({ persona, onEdit, onDelete, onDuplicate }: PersonaCardProps) {
  const color = persona.color || '#8b5cf6'
  const slug = persona.icon_slug || 'Bot'
  const IconCmp = (LucideIcons as unknown as Record<string, React.FC<{ size?: number }>>)[slug] || Bot

  return (
    <div
      className="group relative flex flex-col gap-3 rounded-[12px] border border-border-faint bg-bg2 p-4 transition-colors hover:border-border"
    >
      <div className="flex items-start gap-3">
        <span
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[9px]"
          style={{ background: `${color}22`, color }}
        >
          <IconCmp size={18} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="truncate text-[14px] font-semibold text-text">{persona.name}</div>
          <div className="mt-0.5 text-[11px] uppercase tracking-wider text-text-faint">
            {persona.role}
          </div>
        </div>
      </div>

      {persona.description && (
        <p className="line-clamp-3 text-[12.5px] leading-relaxed text-text-mute">
          {persona.description}
        </p>
      )}

      <div className="mt-auto flex items-center justify-between text-[11px] text-text-faint">
        <span className="truncate">
          {persona.default_model || persona.default_provider || 'no model set'}
        </span>
        <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            className="rounded-[6px] p-1.5 text-text-mute hover:bg-surface hover:text-text"
            title="Edit persona"
            onClick={() => onEdit(persona)}
          >
            <Pencil size={13} />
          </button>
          <button
            className="rounded-[6px] p-1.5 text-text-mute hover:bg-surface hover:text-text"
            title="Duplicate persona"
            onClick={() => onDuplicate(persona)}
          >
            <Copy size={13} />
          </button>
          <button
            className="rounded-[6px] p-1.5 text-text-mute hover:bg-[var(--err)]/10 hover:text-[var(--err)]"
            title="Delete persona"
            onClick={() => onDelete(persona)}
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>
    </div>
  )
}

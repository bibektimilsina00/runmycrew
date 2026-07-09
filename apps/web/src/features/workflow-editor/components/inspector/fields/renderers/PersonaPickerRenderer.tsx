import { useMemo, useState } from 'react'
import * as LucideIcons from 'lucide-react'
import { Bot, ChevronDown, Plus, X } from 'lucide-react'
import { cn } from '@/lib/cn'
import { usePersonas } from '@/features/personas/hooks/usePersonas'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { RendererProps } from '../types'
import type { Persona } from '@/features/personas/types/personaTypes'

/**
 * Picks a saved persona and stores its id on the node.
 *
 * The Agent runtime reads persona_id and overlays the persona's role,
 * system prompt, model, tools onto the node — the user can still override
 * each field per-node.
 */
export function PersonaPickerRenderer({ value, onChange, disabled }: RendererProps) {
  const { data: personas = [], isLoading } = usePersonas()
  const [open, setOpen] = useState(false)
  const currentId = typeof value === 'string' ? value : ''
  const current = useMemo(
    () => personas.find(p => p.id === currentId),
    [personas, currentId],
  )

  const clear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange('')
  }

  return (
    <div className="relative">
      <button
        type="button"
        className={cn(
          'flex w-full items-center gap-2 rounded-[8px] border border-border bg-bg2 px-3 py-2 text-left transition-colors',
          'hover:border-border-strong disabled:cursor-not-allowed disabled:opacity-60',
          open && 'border-accent',
        )}
        disabled={disabled}
        onClick={() => setOpen(v => !v)}
      >
        {current ? (
          <PersonaChip persona={current} />
        ) : (
          <>
            <Bot size={14} className="text-text-faint" />
            <span className="flex-1 text-[13px] text-text-faint">No persona (use node fields)</span>
          </>
        )}
        {current && (
          <button
            type="button"
            onClick={clear}
            className="rounded-[5px] p-0.5 text-text-faint hover:bg-surface hover:text-text"
            title="Clear persona"
          >
            <X size={12} />
          </button>
        )}
        <ChevronDown size={14} className="text-text-faint" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute left-0 right-0 top-[calc(100%+4px)] z-50 max-h-[280px] overflow-y-auto rounded-[10px] border border-border bg-bg2 p-1 shadow-[0_14px_36px_-12px_rgba(0,0,0,0.45)]">
            {isLoading ? (
              <p className="p-3 text-[12px] text-text-faint">Loading personas…</p>
            ) : personas.length === 0 ? (
              <div className="flex flex-col items-start gap-2 p-3">
                <p className="text-[12px] text-text-mute">No personas yet.</p>
                <a
                  href={APP_ROUTES.PERSONAS}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-[12px] text-accent hover:underline"
                >
                  <Plus size={12} />
                  Create your first persona
                </a>
              </div>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => {
                    onChange('')
                    setOpen(false)
                  }}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-[7px] px-2 py-1.5 text-left text-[12.5px] text-text-mute hover:bg-surface hover:text-text',
                    !currentId && 'bg-surface text-text',
                  )}
                >
                  <span className="flex h-6 w-6 items-center justify-center rounded-[6px] bg-bg text-text-faint">
                    <X size={12} />
                  </span>
                  None
                </button>
                {personas.map(p => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      onChange(p.id)
                      setOpen(false)
                    }}
                    className={cn(
                      'flex w-full items-start gap-2 rounded-[7px] px-2 py-1.5 text-left transition-colors hover:bg-surface',
                      p.id === currentId && 'bg-surface',
                    )}
                  >
                    <PersonaChip persona={p} compact />
                  </button>
                ))}
              </>
            )}
            <div className="mt-1 border-t border-border-faint px-2 py-1.5">
              <a
                href={APP_ROUTES.PERSONAS}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-[11.5px] text-text-mute hover:text-text"
              >
                <Plus size={11} />
                Manage personas
              </a>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function PersonaChip({ persona, compact = false }: { persona: Persona; compact?: boolean }) {
  const color = persona.color || '#8b5cf6'
  const slug = persona.icon_slug || 'Bot'
  const IconCmp = (LucideIcons as unknown as Record<string, React.FC<{ size?: number }>>)[slug] || Bot
  return (
    <>
      <span
        className={cn(
          'flex shrink-0 items-center justify-center rounded-[6px]',
          compact ? 'h-6 w-6' : 'h-7 w-7',
        )}
        style={{ background: `${color}22`, color }}
      >
        <IconCmp size={compact ? 12 : 14} />
      </span>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13px] font-medium text-text">{persona.name}</div>
        <div className="truncate text-[10.5px] uppercase tracking-wider text-text-faint">
          {persona.role}
        </div>
      </div>
    </>
  )
}

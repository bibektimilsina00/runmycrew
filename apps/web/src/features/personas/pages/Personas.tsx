import { useMemo, useState } from 'react'
import * as LucideIcons from 'lucide-react'
import { Globe, Plus, Search, Sparkles } from 'lucide-react'
import { Button, useConfirm } from '@/shared/components'
import {
  usePersonas,
  useDeletePersona,
  useCreatePersona,
  useImportPersona,
  usePublicPersonas,
} from '../hooks/usePersonas'
import { PERSONA_PRESETS, type Persona, type PersonaCreateRequest } from '../types/personaTypes'
import { PersonaCard } from '../components/PersonaCard'
import { PersonaEditor } from '../components/PersonaEditor'

export function Personas() {
  const { data: personas = [], isLoading } = usePersonas()
  const [query, setQuery] = useState('')
  const [editing, setEditing] = useState<Persona | null>(null)
  const [seed, setSeed] = useState<PersonaCreateRequest | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const del = useDeletePersona()
  const create = useCreatePersona()
  const importPersona = useImportPersona()
  const { data: publicPersonas = [] } = usePublicPersonas()
  const confirm = useConfirm()

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return personas
    return personas.filter(p =>
      p.name.toLowerCase().includes(q)
      || p.role.toLowerCase().includes(q)
      || (p.description ?? '').toLowerCase().includes(q),
    )
  }, [personas, query])

  const openNew = (from?: PersonaCreateRequest) => {
    setEditing(null)
    setSeed(from ?? null)
    setEditorOpen(true)
  }

  const openEdit = (p: Persona) => {
    setEditing(p)
    setSeed(null)
    setEditorOpen(true)
  }

  const handleDelete = async (p: Persona) => {
    const ok = await confirm({
      title: 'Delete persona?',
      message: `${p.name} will be removed. Existing agent nodes that reference it will fall back to their own settings.`,
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (ok) del.mutate(p.id)
  }

  const handleDuplicate = async (p: Persona) => {
    await create.mutateAsync({
      name: `${p.name} (copy)`,
      role: p.role,
      description: p.description ?? undefined,
      system_prompt: p.system_prompt,
      default_provider: p.default_provider,
      default_model: p.default_model,
      tools: p.tools,
      color: p.color,
      icon_slug: p.icon_slug,
      temperature: p.temperature,
      max_iterations: p.max_iterations,
    })
  }

  const usedRoles = new Set(personas.map(p => p.role))
  const suggestions = PERSONA_PRESETS.filter(p => !usedRoles.has(p.role))

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border-faint bg-bg2 px-8 py-6">
        <div className="mx-auto flex max-w-6xl items-end justify-between gap-6">
          <div>
            <h1 className="text-[22px] font-semibold tracking-tight text-text">Personas</h1>
            <p className="mt-1 text-[13px] text-text-mute">
              Reusable named agents. Pick one on an Agent node to prefill its role, system prompt, model, and tools.
            </p>
          </div>
          <Button onClick={() => openNew()}>
            <Plus size={14} />
            New persona
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mx-auto flex max-w-6xl flex-col gap-6">
          {personas.length > 0 && (
            <div className="flex h-9 items-center gap-2 rounded-[8px] border border-border-faint bg-bg px-3">
              <Search size={14} className="shrink-0 text-text-faint" />
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Filter by name, role, or description…"
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

          {isLoading ? (
            <p className="text-[12.5px] text-text-faint">Loading…</p>
          ) : personas.length === 0 ? (
            <EmptyState onCreate={openNew} suggestions={PERSONA_PRESETS} />
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map(p => (
                <PersonaCard
                  key={p.id}
                  persona={p}
                  onEdit={openEdit}
                  onDelete={handleDelete}
                  onDuplicate={handleDuplicate}
                />
              ))}
            </div>
          )}

          {publicPersonas.length > 0 && (
            <section className="mt-4 border-t border-border-faint pt-6">
              <div className="mb-3 flex items-center gap-2">
                <Globe size={14} className="text-text-mute" />
                <h2 className="text-[13px] font-semibold text-text">Shared library</h2>
                <span className="text-[11px] text-text-faint">
                  personas other workspaces made public — tap to import a copy
                </span>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {publicPersonas.map(p => {
                  const color = p.color || '#8b5cf6'
                  const slug = p.icon_slug || 'Globe'
                  const IconCmp = (LucideIcons as unknown as Record<string, React.FC<{ size?: number }>>)[slug] || Globe

                  return (
                    <button
                      key={p.id}
                      onClick={() => importPersona.mutate(p.id)}
                      disabled={importPersona.isPending}
                      className="group relative flex flex-col gap-3 rounded-[12px] border border-dashed border-border-faint bg-bg2/60 p-4 text-left transition-colors hover:border-border hover:bg-bg2 disabled:opacity-60"
                    >
                      <div className="flex items-start gap-3">
                        <span
                          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[9px]"
                          style={{ background: `${color}22`, color }}
                        >
                          <IconCmp size={18} />
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-[14px] font-semibold text-text">{p.name}</div>
                          <div className="mt-0.5 text-[11px] uppercase tracking-wider text-text-faint">{p.role}</div>
                        </div>
                      </div>
                      {p.description && (
                        <p className="line-clamp-3 text-[12.5px] leading-relaxed text-text-mute">
                          {p.description}
                        </p>
                      )}
                    </button>
                  )
                })}
              </div>
            </section>
          )}

          {personas.length > 0 && suggestions.length > 0 && (
            <section className="mt-4 border-t border-border-faint pt-6">
              <div className="mb-3 flex items-center gap-2">
                <Sparkles size={14} className="text-text-mute" />
                <h2 className="text-[13px] font-semibold text-text">Starter templates</h2>
                <span className="text-[11px] text-text-faint">tap to spin up a new persona</span>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {suggestions.map(s => {
                  const color = s.color || '#8b5cf6'
                  const slug = s.icon_slug || 'Users'
                  const IconCmp = (LucideIcons as unknown as Record<string, React.FC<{ size?: number }>>)[slug] || LucideIcons.Users

                  return (
                    <button
                      key={s.role}
                      onClick={() => openNew(s)}
                      className="group relative flex flex-col gap-3 rounded-[12px] border border-dashed border-border-faint bg-bg2/60 p-4 text-left transition-colors hover:border-border hover:bg-bg2"
                    >
                      <div className="flex items-start gap-3">
                        <span
                          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[9px]"
                          style={{ background: `${color}22`, color }}
                        >
                          <IconCmp size={18} />
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-[14px] font-semibold text-text">{s.name}</div>
                          <div className="mt-0.5 text-[11px] uppercase tracking-wider text-text-faint">{s.role}</div>
                        </div>
                      </div>
                      {s.description && (
                        <p className="line-clamp-3 text-[12.5px] leading-relaxed text-text-mute">
                          {s.description}
                        </p>
                      )}
                    </button>
                  )
                })}
              </div>
            </section>
          )}
        </div>
      </div>

      <PersonaEditor
        key={editing ? `edit-${editing.id}` : `new-${seed?.role ?? 'blank'}`}
        open={editorOpen}
        persona={editing}
        seed={seed}
        onClose={() => setEditorOpen(false)}
      />
    </div>
  )
}

function EmptyState({ onCreate, suggestions }: { onCreate: (seed?: PersonaCreateRequest) => void; suggestions: PersonaCreateRequest[] }) {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col items-center gap-3 rounded-[12px] border border-dashed border-border-faint bg-bg p-10 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-[10px] bg-accent/10 text-accent">
          <LucideIcons.Users size={20} />
        </div>
        <h2 className="text-[15px] font-semibold text-text">No personas yet</h2>
        <p className="max-w-md text-[12.5px] text-text-mute">
          A persona is a named agent — role, system prompt, model, tools — that any Agent node in your crews can adopt with one click.
          Start from a template or build your own.
        </p>
        <Button onClick={() => onCreate()}>
          <Plus size={14} />
          Build your own
        </Button>
      </div>

      <div>
        <div className="mb-3 flex items-center gap-2">
          <Sparkles size={14} className="text-text-mute" />
          <h2 className="text-[13px] font-semibold text-text">Starter templates</h2>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {suggestions.map(s => {
            const color = s.color || '#8b5cf6'
            const slug = s.icon_slug || 'Users'
            const IconCmp = (LucideIcons as unknown as Record<string, React.FC<{ size?: number }>>)[slug] || LucideIcons.Users

            return (
              <button
                key={s.role}
                onClick={() => onCreate(s)}
                className="group relative flex flex-col gap-3 rounded-[12px] border border-border-faint bg-bg2 p-4 text-left transition-colors hover:border-border"
              >
                <div className="flex items-start gap-3">
                  <span
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[9px]"
                    style={{ background: `${color}22`, color }}
                  >
                    <IconCmp size={18} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[14px] font-semibold text-text">{s.name}</div>
                    <div className="mt-0.5 text-[11px] uppercase tracking-wider text-text-faint">{s.role}</div>
                  </div>
                </div>
                {s.description && (
                  <p className="line-clamp-3 text-[12.5px] leading-relaxed text-text-mute">
                    {s.description}
                  </p>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

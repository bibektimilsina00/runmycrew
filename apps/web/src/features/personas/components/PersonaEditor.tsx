import { useState } from 'react'
import { Modal, Input, Textarea, Button } from '@/shared/components'
import type { Persona, PersonaCreateRequest } from '../types/personaTypes'
import { useCreatePersona, useUpdatePersona } from '../hooks/usePersonas'

interface PersonaEditorProps {
  open: boolean
  persona?: Persona | null
  seed?: PersonaCreateRequest | null
  onClose: () => void
  onSaved?: (id: string) => void
}

const ROLE_SUGGESTIONS = ['researcher', 'planner', 'writer', 'reviewer', 'coder', 'critic', 'analyst', 'summarizer']

const emptyForm: PersonaCreateRequest = {
  name: '',
  role: 'researcher',
  description: '',
  system_prompt: '',
  default_provider: 'openai',
  default_model: '',
  tools: [],
  color: '#8b5cf6',
  icon_slug: 'Bot',
  temperature: 0.3,
  max_iterations: 10,
  is_public: false,
}

export function PersonaEditor({ open, persona, seed, onClose, onSaved }: PersonaEditorProps) {
  const [form, setForm] = useState<PersonaCreateRequest>(() => {
    if (persona) {
      return {
        name: persona.name,
        role: persona.role,
        description: persona.description ?? '',
        system_prompt: persona.system_prompt,
        default_provider: persona.default_provider,
        default_model: persona.default_model,
        tools: persona.tools,
        color: persona.color,
        icon_slug: persona.icon_slug,
        temperature: persona.temperature,
        max_iterations: persona.max_iterations,
        is_public: persona.is_public,
      }
    }
    if (seed) return { ...emptyForm, ...seed }
    return emptyForm
  })
  const create = useCreatePersona()
  const update = useUpdatePersona(persona?.id ?? '')
  const busy = create.isPending || update.isPending

  const patch = <K extends keyof PersonaCreateRequest>(key: K, value: PersonaCreateRequest[K]) => {
    setForm(f => ({ ...f, [key]: value }))
  }

  const submit = async () => {
    if (!form.name.trim() || !form.role.trim()) return
    try {
      if (persona) {
        const saved = await update.mutateAsync(form)
        onSaved?.(saved.id)
      } else {
        const created = await create.mutateAsync(form)
        onSaved?.(created.id)
      }
      onClose()
    } catch {
      // hook exposes error state
    }
  }

  return (
    <Modal
      open={open}
      onClose={busy ? () => {} : onClose}
      title={persona ? 'Edit persona' : 'New persona'}
      description="Reusable named agent — role, system prompt, default model and tools."
      width="880px"
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!form.name.trim() || !form.role.trim() || busy}>
            {busy ? 'Saving…' : persona ? 'Save persona' : 'Create persona'}
          </Button>
        </div>
      }
    >
      {/* Fixed body height so the modal doesn't jump when the system-prompt
          textarea grows. Two columns: identity + config on the left, system
          prompt + share on the right. */}
      <div className="grid h-[520px] grid-cols-[1fr_1.15fr] gap-6 overflow-y-auto pr-1">
        {/* ── Left column: identity + defaults ─────────────────── */}
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Name">
              <Input
                value={form.name}
                onChange={e => patch('name', e.target.value)}
                placeholder="Senior Code Reviewer"
                autoFocus
                maxLength={128}
              />
            </Field>
            <Field label="Role" hint="Short tag: researcher, reviewer…">
              <Input
                value={form.role}
                onChange={e => patch('role', e.target.value.toLowerCase().replace(/\s+/g, '_'))}
                placeholder="reviewer"
                maxLength={64}
                list="persona-role-suggestions"
              />
              <datalist id="persona-role-suggestions">
                {ROLE_SUGGESTIONS.map(r => (
                  <option key={r} value={r} />
                ))}
              </datalist>
            </Field>
          </div>

          <Field label="Description">
            <Textarea
              value={form.description ?? ''}
              onChange={e => patch('description', e.target.value)}
              placeholder="Short summary of what this persona does."
              rows={2}
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Default provider">
              <Input
                value={form.default_provider ?? ''}
                onChange={e => patch('default_provider', e.target.value)}
                placeholder="openai"
              />
            </Field>
            <Field label="Default model">
              <Input
                value={form.default_model ?? ''}
                onChange={e => patch('default_model', e.target.value)}
                placeholder="claude-sonnet-4-6"
              />
            </Field>
            <Field label="Temperature">
              <Input
                type="number"
                min={0}
                max={2}
                step={0.1}
                value={form.temperature ?? 0.3}
                onChange={e => patch('temperature', Number(e.target.value))}
              />
            </Field>
            <Field label="Max iterations">
              <Input
                type="number"
                min={1}
                max={50}
                value={form.max_iterations ?? 10}
                onChange={e => patch('max_iterations', Number(e.target.value))}
              />
            </Field>
          </div>

          <div className="grid grid-cols-[1fr_92px] items-end gap-3">
            <Field label="Icon slug" hint="lucide icon: Bot, PenLine, Shield…">
              <Input
                value={form.icon_slug ?? ''}
                onChange={e => patch('icon_slug', e.target.value)}
                placeholder="Bot"
              />
            </Field>
            <Field label="Color">
              <Input
                type="color"
                value={form.color ?? '#8b5cf6'}
                onChange={e => patch('color', e.target.value)}
                className="h-9 !p-1"
              />
            </Field>
          </div>
        </div>

        {/* ── Right column: system prompt + share ──────────────── */}
        <div className="flex flex-col gap-4">
          <Field label="System prompt" hint="Baked-in behavior contract; overlaid onto the agent node when picked.">
            <Textarea
              value={form.system_prompt ?? ''}
              onChange={e => patch('system_prompt', e.target.value)}
              placeholder="You are a rigorous reviewer. Score work on correctness, clarity, and completeness…"
              rows={13}
              className="min-h-[300px] resize-none"
            />
          </Field>

          <label className="flex items-start gap-3 rounded-[10px] border border-border-faint bg-bg2 p-3">
            <input
              type="checkbox"
              checked={!!form.is_public}
              onChange={e => patch('is_public', e.target.checked)}
              className="mt-0.5"
            />
            <div>
              <div className="text-[13px] font-medium text-text">Share publicly</div>
              <div className="text-[11.5px] text-text-mute">
                Other workspaces can import a copy from the shared library. Your original stays editable.
              </div>
            </div>
          </label>
        </div>
      </div>
    </Modal>
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[11px] font-medium uppercase tracking-wider text-text-mute">{label}</span>
      {children}
      {hint && <span className="text-[11px] text-text-faint">{hint}</span>}
    </label>
  )
}

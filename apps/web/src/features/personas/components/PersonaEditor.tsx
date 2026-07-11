import { useState } from 'react'
import * as LucideIcons from 'lucide-react'
import { Modal, Input, Textarea, Button, FormField, Checkbox, ColorPicker, Tooltip } from '@/shared/components'
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

const FieldLabel = ({ text, tooltip }: { text: string; tooltip?: string }) => (
  <div className="flex items-center gap-1.5 text-xs font-semibold text-text-mute select-none mb-1">
    <span>{text}</span>
    {tooltip && (
      <Tooltip content={tooltip}>
        <LucideIcons.HelpCircle size={13} className="text-text-faint hover:text-text-mute cursor-help transition-colors" />
      </Tooltip>
    )}
  </div>
)

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
      width="900px"
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
      <div className="grid grid-cols-1 md:grid-cols-[1.1fr_1fr] gap-8 h-[420px] pr-1">
        {/* ── Left Column: Identity & Settings ─────────────────── */}
        <div className="flex flex-col gap-4 h-full justify-between">
          <div className="grid grid-cols-2 gap-4">
            <FormField required>
              <FieldLabel text="Name" />
              <Input
                value={form.name}
                onChange={e => patch('name', e.target.value)}
                placeholder="Senior Code Reviewer"
                autoFocus
                maxLength={128}
              />
            </FormField>
            <FormField required>
              <FieldLabel text="Role" tooltip="Short tag matching the agent's task: e.g. researcher, reviewer, coder" />
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
            </FormField>
          </div>

          <FormField>
            <FieldLabel text="Description" />
            <Textarea
              value={form.description ?? ''}
              onChange={e => patch('description', e.target.value)}
              placeholder="Short summary of what this persona does."
              rows={2}
              className="resize-none bg-[#262626]"
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField>
              <FieldLabel text="Default Provider" />
              <Input
                value={form.default_provider ?? ''}
                onChange={e => patch('default_provider', e.target.value)}
                placeholder="openai"
              />
            </FormField>
            <FormField>
              <FieldLabel text="Default Model" />
              <Input
                value={form.default_model ?? ''}
                onChange={e => patch('default_model', e.target.value)}
                placeholder="claude-sonnet-4-6"
              />
            </FormField>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <FormField>
              <FieldLabel text="Icon Slug" tooltip="Lucide icon name (Bot, PenLine, Shield, Code...)" />
              <Input
                value={form.icon_slug ?? ''}
                onChange={e => patch('icon_slug', e.target.value)}
                placeholder="Bot"
              />
            </FormField>
            <FormField>
              <FieldLabel text="Temperature" />
              <Input
                type="number"
                min={0}
                max={2}
                step={0.1}
                value={form.temperature ?? 0.3}
                onChange={e => patch('temperature', Number(e.target.value))}
              />
            </FormField>
            <FormField>
              <FieldLabel text="Max Iterations" />
              <Input
                type="number"
                min={1}
                max={50}
                value={form.max_iterations ?? 10}
                onChange={e => patch('max_iterations', Number(e.target.value))}
              />
            </FormField>
          </div>

          <FormField>
            <FieldLabel text="Color Theme" />
            <div className="flex h-9 items-center">
              <ColorPicker
                value={form.color ?? null}
                onChange={val => patch('color', val)}
              />
            </div>
          </FormField>
        </div>

        {/* ── Right Column: Prompt & Sharing ─────────────────── */}
        <div className="flex flex-col gap-4 h-full justify-between">
          <div className="flex flex-col flex-1 min-h-0 gap-1">
            <FieldLabel text="System Prompt" tooltip="Baked-in behavior contract; overlaid onto the agent node when picked." />
            <Textarea
              value={form.system_prompt ?? ''}
              onChange={e => patch('system_prompt', e.target.value)}
              placeholder="You are a rigorous reviewer. Score work on correctness, clarity, and completeness…"
              className="flex-1 min-h-0 resize-none bg-[#262626]"
            />
          </div>

          <div className="flex items-center gap-4 rounded-[10px] border border-border-faint bg-bg2/40 p-3 h-[58px] shrink-0">
            <Checkbox
              checked={!!form.is_public}
              onChange={e => patch('is_public', e.target.checked)}
              label="Share publicly"
            />
            <span className="text-[11px] text-text-faint flex-1">
              Workspaces can import a copy from the shared library.
            </span>
          </div>
        </div>
      </div>
    </Modal>
  )
}

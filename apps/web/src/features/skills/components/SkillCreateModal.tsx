import { useState } from 'react'
import { Modal, Input, Textarea, Button } from '@/shared/components'
import { useCreateSkill } from '../hooks/useSkills'

interface SkillCreateModalProps {
  open: boolean
  onClose: () => void
  onCreated?: (id: string) => void
}

const DEFAULT_ICON = 'BookOpen'
const DEFAULT_COLOR = '#8b5cf6'

const COLOR_SWATCHES = [
  '#8b5cf6', // violet
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#ec4899', // pink
  '#14b8a6', // teal
  '#64748b', // slate
]

export function SkillCreateModal({ open, onClose, onCreated }: SkillCreateModalProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [color, setColor] = useState(DEFAULT_COLOR)
  const create = useCreateSkill()

  const reset = () => {
    setName('')
    setDescription('')
    setColor(DEFAULT_COLOR)
  }

  const close = () => {
    if (create.isPending) return
    reset()
    onClose()
  }

  const submit = async () => {
    const trimmed = name.trim()
    if (!trimmed) return
    try {
      const created = await create.mutateAsync({
        name: trimmed,
        description: description.trim(),
        icon: DEFAULT_ICON,
        color,
        content: `# ${trimmed}\n\nDescribe how the agent should use this skill, then add the body of the instructions below.\n`,
      })
      reset()
      onClose()
      onCreated?.(created.id)
    } catch {
      // mutation surfaces error state via `create.isError`
    }
  }

  return (
    <Modal
      open={open}
      onClose={close}
      title="New skill"
      description="Reusable instructions an AI agent can load on demand."
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={close} disabled={create.isPending}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!name.trim() || create.isPending}>
            {create.isPending ? 'Creating…' : 'Create skill'}
          </Button>
        </div>
      }
    >
      <div className="flex flex-col gap-3">
        <Field label="Name">
          <Input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Customer support escalation"
            autoFocus
            maxLength={64}
          />
        </Field>

        <Field label="Description">
          <Textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Short summary of when the agent should use this skill."
            rows={2}
            maxLength={1024}
          />
        </Field>

        <Field label="Color">
          <div className="flex flex-wrap gap-1.5">
            {COLOR_SWATCHES.map(swatch => (
              <button
                key={swatch}
                type="button"
                onClick={() => setColor(swatch)}
                className="h-7 w-7 rounded-[6px] transition-transform hover:scale-110"
                style={{
                  background: swatch,
                  boxShadow: color === swatch ? `0 0 0 2px var(--bg2), 0 0 0 4px ${swatch}` : undefined,
                }}
                aria-label={`Pick ${swatch}`}
                aria-pressed={color === swatch}
              />
            ))}
          </div>
        </Field>

        {create.isError && (
          <p className="text-[11px] text-err">
            {create.error instanceof Error ? create.error.message : 'Failed to create skill.'}
          </p>
        )}
      </div>
    </Modal>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] font-semibold uppercase tracking-wide text-text-mute">
        {label}
      </span>
      {children}
    </label>
  )
}

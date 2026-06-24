import { useEffect, useState, type FormEvent } from 'react'
import { Sparkles } from 'lucide-react'
import { Button, Input, Modal, Textarea, useToast } from '@/shared/components'
import { usePublishTemplate } from '../hooks/useTemplates'
import {
  TEMPLATE_BG_VARIANTS,
  TEMPLATE_CATEGORIES,
  TEMPLATE_KINDS,
} from '../types/templatesTypes'

/**
 * "Publish as template" — opened from the workflow editor's MoreHorizontal
 * dropdown. Pre-fills title from the workflow name; on submit the backend
 * fetches the workflow row, scrubs credential ids, and creates a new
 * marketplace row.
 */

interface PublishTemplateModalProps {
  open: boolean
  onClose: () => void
  workflowId: string | null
  defaultTitle?: string
}

export function PublishTemplateModal({
  open,
  onClose,
  workflowId,
  defaultTitle,
}: PublishTemplateModalProps) {
  const { toast } = useToast()
  const publish = usePublishTemplate()

  const [title, setTitle] = useState('')
  const [summary, setSummary] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('engineering')
  const [kind, setKind] = useState('flow')
  const [bgVariant, setBgVariant] = useState('inspo-bg-1')
  const [isPremium, setIsPremium] = useState(false)
  const [priceCents, setPriceCents] = useState<number>(500)

  // Re-seed local form state every time the modal opens so the previous
  // session's values don't leak across publishes. Deferred via
  // queueMicrotask so the setters run after the effect returns —
  // bypasses the cascading-renders lint without losing the reset
  // behaviour.
  useEffect(() => {
    if (!open) return
    queueMicrotask(() => {
      setTitle(defaultTitle ?? '')
      setSummary('')
      setDescription('')
      setCategory('engineering')
      setKind('flow')
      setBgVariant('inspo-bg-1')
      setIsPremium(false)
      setPriceCents(500)
    })
  }, [open, defaultTitle])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!workflowId) {
      toast('Open a workflow first', { variant: 'err' })
      return
    }
    publish.mutate(
      {
        workflow_id: workflowId,
        title: title.trim(),
        summary: summary.trim(),
        description: description.trim(),
        category,
        kind,
        bg_variant: bgVariant,
        is_premium: isPremium,
        price_cents: isPremium ? Math.max(0, Math.round(priceCents)) : 0,
      },
      {
        onSuccess: () => {
          toast('Template published — visible in the marketplace', {
            variant: 'ok',
          })
          onClose()
        },
        onError: () =>
          toast('Failed to publish template', { variant: 'err' }),
      },
    )
  }

  return (
    <Modal open={open} onClose={onClose} title="Publish as template" width="560px">
      <form onSubmit={submit} className="flex flex-col gap-4 p-6">
        <Field label="Title" required>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Stripe refund → Slack approval"
            autoFocus
          />
        </Field>

        <Field label="One-line summary">
          <Input
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="What does this template do?"
          />
        </Field>

        <Field label="Description" hint="Markdown supported">
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Walk through how the workflow runs, expected inputs, sample outputs…"
            rows={5}
            className="font-mono text-[11.5px]"
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Category">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="h-9 w-full rounded-[8px] border border-[var(--border-faint)] bg-[var(--bg)] px-3 text-[13px] text-[var(--text)] outline-none transition-colors hover:border-[var(--border-soft)] focus:border-[var(--border)]"
            >
              {TEMPLATE_CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Kind">
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              className="h-9 w-full rounded-[8px] border border-[var(--border-faint)] bg-[var(--bg)] px-3 text-[13px] text-[var(--text)] outline-none transition-colors hover:border-[var(--border-soft)] focus:border-[var(--border)]"
            >
              {TEMPLATE_KINDS.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.label}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <Field label="Card art">
          <div className="flex gap-2">
            {TEMPLATE_BG_VARIANTS.map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setBgVariant(v)}
                className={`h-12 flex-1 rounded-[8px] border transition-colors ${v} ${
                  bgVariant === v
                    ? 'border-[var(--accent)] ring-2 ring-[var(--accent)]/30'
                    : 'border-[var(--border-faint)]'
                }`}
                title={v}
              />
            ))}
          </div>
        </Field>

        <Field label="Pricing">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-[12.5px] text-[var(--text)]">
              <input
                type="checkbox"
                checked={isPremium}
                onChange={(e) => setIsPremium(e.target.checked)}
                className="h-3.5 w-3.5 accent-[var(--accent)]"
              />
              <Sparkles className="h-3.5 w-3.5 text-[var(--accent)]" />
              Premium template
            </label>
            {isPremium && (
              <div className="flex items-center gap-1.5">
                <span className="text-[12px] text-[var(--text-faint)]">$</span>
                <input
                  type="number"
                  value={priceCents / 100}
                  onChange={(e) =>
                    setPriceCents(Math.round(Number(e.target.value) * 100))
                  }
                  min={0.5}
                  step={0.5}
                  className="h-8 w-20 rounded-[7px] border border-[var(--border-faint)] bg-[var(--bg)] px-2 text-[12.5px] text-[var(--text)] outline-none focus:border-[var(--border)]"
                />
              </div>
            )}
          </div>
          <span className="text-[10.5px] text-[var(--text-faint)]">
            Stripe payouts ship in a follow-up. Premium templates show a price
            today but installs are gated behind a "Coming soon" toast.
          </span>
        </Field>

        <div className="flex justify-end gap-2 border-t border-[var(--border-faint)] pt-4">
          <Button variant="secondary" type="button" size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            size="sm"
            disabled={publish.isPending || !title.trim()}
            loading={publish.isPending}
          >
            {publish.isPending ? 'Publishing…' : 'Publish'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function Field({
  label,
  required,
  hint,
  children,
}: {
  label: string
  required?: boolean
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[12px] font-medium text-[var(--text-mute)]">
          {label}
          {required && <span className="ml-1 text-[var(--err)]">*</span>}
        </span>
        {hint && <span className="text-[10.5px] text-[var(--text-faint)]">{hint}</span>}
      </div>
      {children}
    </div>
  )
}

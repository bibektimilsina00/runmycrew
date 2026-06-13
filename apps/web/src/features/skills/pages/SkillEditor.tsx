import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Trash2, Loader2 } from 'lucide-react'
import { Button, Input, Textarea, Spinner } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { cn } from '@/lib/cn'
import { useCreateSkill, useDeleteSkill, useSkill, useUpdateSkill } from '../hooks/useSkills'
import { SkillContentEditor } from '../components/SkillContentEditor'
import { SkillIconPicker } from '../components/SkillIconPicker'
import { SkillIconBadge } from '../components/SkillIconBadge'
import { SkillDeleteConfirmModal } from '../components/SkillDeleteConfirmModal'
import type { Skill, SkillMeta } from '../types/skillTypes'

const DEFAULT_ICON = 'BookOpen'

interface Draft {
  name: string
  description: string
  icon: string
  content: string
}

const BLANK_DRAFT: Draft = {
  name: '',
  description: '',
  icon: DEFAULT_ICON,
  content: '',
}

function draftFromSkill(skill: Skill): Draft {
  return {
    name: skill.name,
    description: skill.description,
    icon: skill.icon,
    content: skill.content,
  }
}

function isDirty(draft: Draft, baseline: Draft): boolean {
  return (
    draft.name !== baseline.name ||
    draft.description !== baseline.description ||
    draft.icon !== baseline.icon ||
    draft.content !== baseline.content
  )
}

export function SkillEditor() {
  const params = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isNew = !params.id || params.id === 'new'

  const skillQuery = useSkill(isNew ? null : params.id)
  const create = useCreateSkill()
  const update = useUpdateSkill()
  const del = useDeleteSkill()

  // Baseline is derived directly from the server payload — it's the
  // "last saved" snapshot and stays in sync without an effect. The draft
  // is local state that resets whenever the underlying skill identity
  // changes (mode flip or navigating to a different skill id).
  const baseline = useMemo<Draft>(() => {
    if (isNew || !skillQuery.data) return BLANK_DRAFT
    return draftFromSkill(skillQuery.data)
  }, [isNew, skillQuery.data])

  const currentSkillKey = isNew ? '__new__' : skillQuery.data?.id ?? null

  const [draft, setDraft] = useState<Draft>(baseline)
  const [lastSkillKey, setLastSkillKey] = useState<string | null>(currentSkillKey)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // React's "adjusting state when a prop changes" pattern: when the
  // identity of the skill we're editing flips, hydrate the draft from
  // the new baseline in render rather than via useEffect.
  if (currentSkillKey !== lastSkillKey) {
    setLastSkillKey(currentSkillKey)
    setDraft(baseline)
  }

  const dirty = useMemo(() => isDirty(draft, baseline), [draft, baseline])
  const saving = create.isPending || update.isPending

  const update_ = (patch: Partial<Draft>) => setDraft(d => ({ ...d, ...patch }))

  const save = async () => {
    setError(null)
    const trimmedName = draft.name.trim()
    if (!trimmedName) {
      setError('Name is required.')
      return
    }
    const payload = {
      name: trimmedName,
      description: draft.description.trim(),
      icon: draft.icon,
      content: draft.content,
    }
    try {
      if (isNew) {
        const created = await create.mutateAsync(payload)
        navigate(APP_ROUTES.SKILL_EDIT(created.id), { replace: true })
      } else if (params.id) {
        // useUpdateSkill writes the response to the query cache, which flows
        // through to `baseline` automatically — no local setBaseline needed.
        const updated = await update.mutateAsync({ id: params.id, data: payload })
        setDraft(draftFromSkill(updated))
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save skill.')
    }
  }

  const back = () => navigate(APP_ROUTES.SKILLS)

  // Show a loading skeleton while fetching an existing skill.
  if (!isNew && skillQuery.isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    )
  }

  // Skill id in the URL but server says it doesn't exist.
  if (!isNew && !skillQuery.isLoading && !skillQuery.data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3">
        <p className="text-[13px] text-text-mute">Skill not found.</p>
        <Button onClick={back} variant="ghost">
          <ArrowLeft size={13} />
          Back to skills
        </Button>
      </div>
    )
  }

  const skillForDelete: SkillMeta | null = isNew || !skillQuery.data
    ? null
    : {
        id: skillQuery.data.id,
        name: skillQuery.data.name,
        description: skillQuery.data.description,
        icon: skillQuery.data.icon,
        created_at: skillQuery.data.created_at,
        updated_at: skillQuery.data.updated_at,
      }

  return (
    <div className="flex h-full flex-col">
      {/* Sticky header */}
      <div className="sticky top-0 z-10 border-b border-border-faint bg-bg2 px-6 py-3">
        <div className="mx-auto flex max-w-5xl items-center gap-3">
          <Button variant="ghost" onClick={back} disabled={saving}>
            <ArrowLeft size={13} />
            Skills
          </Button>
          <div className="ml-2 flex min-w-0 items-center gap-2.5">
            <SkillIconBadge iconName={draft.icon} size="sm" />
            <span className="truncate text-[14px] font-semibold text-text">
              {draft.name.trim() || (isNew ? 'New skill' : 'Untitled skill')}
            </span>
            {dirty && (
              <span className="rounded-[4px] bg-warn/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-warn">
                Unsaved
              </span>
            )}
          </div>
          <div className="ml-auto flex items-center gap-2">
            {!isNew && (
              <Button
                variant="ghost"
                onClick={() => setDeleteOpen(true)}
                disabled={saving || del.isPending}
                className="text-err hover:text-err"
              >
                <Trash2 size={13} />
                Delete
              </Button>
            )}
            <Button onClick={save} disabled={!dirty || saving}>
              {saving && <Loader2 size={13} className="animate-spin" />}
              {isNew ? 'Create skill' : 'Save changes'}
            </Button>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Field label="Name" required>
              <Input
                value={draft.name}
                onChange={e => update_({ name: e.target.value })}
                placeholder="Customer support escalation"
                maxLength={64}
                autoFocus={isNew}
              />
            </Field>

            <Field label="Icon">
              <SkillIconPicker
                value={draft.icon}
                onChange={icon => update_({ icon })}
              />
            </Field>

            <Field label="Description" className="md:col-span-2">
              <Textarea
                value={draft.description}
                onChange={e => update_({ description: e.target.value })}
                placeholder="Short summary of when the agent should use this skill."
                rows={2}
                maxLength={1024}
              />
            </Field>
          </div>

          {/* Body editor — takes the rest of the page height */}
          <div className="flex min-h-[400px] flex-col gap-2">
            <div className="flex items-end justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wide text-text-mute">
                Content
              </span>
              <span className="text-[10.5px] text-text-faint">
                Markdown — loaded by the agent on demand via the load_skill tool.
              </span>
            </div>
            <SkillContentEditor
              value={draft.content}
              onChange={content => update_({ content })}
              placeholder={'# Skill name\n\nDescribe how the agent should use this skill.\n'}
              className="min-h-[400px]"
            />
          </div>

          {error && (
            <div className="rounded-[6px] border border-err/40 bg-err/10 px-3 py-2 text-[11.5px] text-err">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Delete confirm modal handles navigation back to /skills on success */}
      <SkillDeleteConfirmModal
        skill={deleteOpen ? skillForDelete : null}
        onClose={() => {
          setDeleteOpen(false)
          // If the skill is gone, bounce out. The query will fail on next
          // refetch — we don't want to keep the editor open on a deleted row.
          if (del.isSuccess) navigate(APP_ROUTES.SKILLS)
        }}
      />
    </div>
  )
}

function Field({
  label,
  required,
  className,
  children,
}: {
  label: string
  required?: boolean
  className?: string
  children: React.ReactNode
}) {
  return (
    <label className={cn('flex flex-col gap-1.5', className)}>
      <span className="text-[11px] font-semibold uppercase tracking-wide text-text-mute">
        {label}
        {required && <span className="ml-1 text-err">*</span>}
      </span>
      {children}
    </label>
  )
}

import { Modal, Button } from '@/shared/components'
import { useDeleteSkill } from '../hooks/useSkills'
import type { SkillMeta } from '../types/skillTypes'

interface Props {
  skill: SkillMeta | null
  onClose: () => void
}

export function SkillDeleteConfirmModal({ skill, onClose }: Props) {
  const del = useDeleteSkill()

  const submit = async () => {
    if (!skill) return
    try {
      await del.mutateAsync(skill.id)
      onClose()
    } catch {
      // surfaced via del.isError below
    }
  }

  return (
    <Modal
      open={!!skill}
      onClose={() => !del.isPending && onClose()}
      title="Delete skill?"
      description={`"${skill?.name ?? ''}" will be removed for every agent that uses it.`}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={del.isPending}>
            Cancel
          </Button>
          <Button variant="danger" onClick={submit} disabled={del.isPending}>
            {del.isPending ? 'Deleting…' : 'Delete'}
          </Button>
        </div>
      }
    >
      <p className="text-[12.5px] text-text-mute">
        This action can't be undone. Agents currently referencing this skill will silently
        ignore it on their next run.
      </p>
      {del.isError && (
        <p className="mt-2 text-[11px] text-err">
          {del.error instanceof Error ? del.error.message : 'Failed to delete.'}
        </p>
      )}
    </Modal>
  )
}

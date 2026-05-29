import { Button, ColorPicker, Input, Modal } from '@/shared/components'
import type { AppLayoutController } from './use-app-layout-controller'

interface WorkflowDialogsProps {
  controller: AppLayoutController
}

export function WorkflowDialogs({ controller }: WorkflowDialogsProps) {
  const state = controller.modalState

  return (
    <>
      <Modal open={state.isCreateFolderOpen} onClose={state.resetCreateFolder} title="Create Folder">
        <form onSubmit={state.submitCreateFolder} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Folder Name</label>
            <Input
              value={state.createFolderName}
              onChange={event => state.setCreateFolderName(event.target.value)}
              placeholder="e.g. Sales, Marketing"
              autoFocus
            />
          </div>
          <DialogFooter
            onCancel={state.resetCreateFolder}
            submitLabel={state.createFolderPending ? 'Creating...' : 'Create'}
            submitDisabled={state.createFolderPending || !state.createFolderName.trim()}
          />
        </form>
      </Modal>

      <Modal open={state.isRenameFolderOpen} onClose={state.resetRenameFolder} title="Rename Folder">
        <form onSubmit={state.submitRenameFolder} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">New Name</label>
            <Input
              value={state.renameFolderName}
              onChange={event => state.setRenameFolderName(event.target.value)}
              placeholder="New name..."
              autoFocus
            />
          </div>
          <DialogFooter
            onCancel={state.resetRenameFolder}
            submitLabel={state.updateFolderPending ? 'Saving...' : 'Rename'}
            submitDisabled={state.updateFolderPending || !state.renameFolderName.trim()}
          />
        </form>
      </Modal>

      <Modal open={state.isCreateWorkflowOpen} onClose={state.resetCreateWorkflow} title="Create Workflow">
        <form onSubmit={state.submitCreateWorkflow} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Workflow Name (Optional)</label>
            <Input
              value={state.createWorkflowName}
              onChange={event => state.setCreateWorkflowName(event.target.value)}
              placeholder="Leave empty for a cool random name"
              autoFocus
            />
          </div>
          <ColorField
            label="Workflow Color (Optional)"
            value={state.createWorkflowColor}
            onChange={state.setCreateWorkflowColor}
          />
          <DialogFooter
            onCancel={state.resetCreateWorkflow}
            submitLabel={state.createWorkflowPending ? 'Creating...' : 'Create'}
            submitDisabled={state.createWorkflowPending}
          />
        </form>
      </Modal>

      <Modal open={state.isRenameWorkflowOpen} onClose={state.resetRenameWorkflow} title="Workflow Settings">
        <form onSubmit={state.submitRenameWorkflow} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">New Name</label>
            <Input
              value={state.renameWorkflowName}
              onChange={event => state.setRenameWorkflowName(event.target.value)}
              placeholder="New name..."
              autoFocus
            />
          </div>
          <ColorField
            label="Workflow Color"
            value={state.renameWorkflowColor}
            onChange={state.setRenameWorkflowColor}
          />
          <DialogFooter
            onCancel={state.resetRenameWorkflow}
            submitLabel={state.updateWorkflowPending ? 'Saving...' : 'Save'}
            submitDisabled={state.updateWorkflowPending || !state.renameWorkflowName.trim()}
          />
        </form>
      </Modal>
    </>
  )
}

function ColorField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string | null
  onChange: (value: string | null) => void
}) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-[12px] font-medium text-[var(--text-mute)]">{label}</label>
      <ColorPicker value={value} onChange={onChange} />
    </div>
  )
}

function DialogFooter({
  onCancel,
  submitLabel,
  submitDisabled,
}: {
  onCancel: () => void
  submitLabel: string
  submitDisabled: boolean
}) {
  return (
    <div className="flex justify-end gap-2 border-t border-[var(--border-faint)] pt-4">
      <Button variant="secondary" type="button" size="sm" onClick={onCancel}>Cancel</Button>
      <Button variant="primary" type="submit" size="sm" disabled={submitDisabled}>{submitLabel}</Button>
    </div>
  )
}

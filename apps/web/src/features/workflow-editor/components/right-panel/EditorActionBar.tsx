import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useParams } from 'react-router-dom'
import {
  MoreHorizontal, MessageCircle, Rocket, Power, Play, Loader2,
  LayoutDashboard, Lock, Download, Copy, Trash2, PanelRightClose,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import { Button } from '@/shared/components'
import { useEditorActionBar } from '../../hooks/useEditorActionBar'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'
import { PublishTemplateModal } from '@/features/templates/components/PublishTemplateModal'
import { ShareAppButton } from '@/features/public-app/components/ShareAppButton'
import { slugifyAppUrl } from '@/features/public-app/utils/slug'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { useToast } from '@/shared/components'

interface EditorActionBarProps {
  onRun: () => void
  isRunning: boolean
}

// ── Portalled dropdown ────────────────────────────────────────────────────────

interface DropdownItem {
  label: string
  icon: React.ReactNode
  onClick: () => void
  variant?: 'danger'
  dividerBefore?: boolean
}

function OptionsDropdown({ anchorRect, items, onClose }: {
  anchorRect: DOMRect
  items: DropdownItem[]
  onClose: () => void
}) {
  const menuW = 220
  const menuH = items.length * 34 + 16
  const left  = anchorRect.right - menuW
  const top   = anchorRect.bottom + 4 + menuH > window.innerHeight
    ? anchorRect.top - menuH - 4
    : anchorRect.bottom + 4

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9998]" onClick={onClose} />
      <div
        className="fixed z-[9999] overflow-hidden rounded-[12px] border border-[var(--border)] bg-[var(--bg-2)] p-1.5 shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]"
        style={{ left, top, width: menuW }}
      >
        {items.map((item, i) => (
          <div key={i}>
            {item.dividerBefore && <div className="my-1 mx-1 h-px bg-[var(--border-faint)]" />}
            <button
              onClick={() => { item.onClick(); onClose() }}
              className={cn(
                'flex w-full items-center gap-2.5 rounded-[7px] px-3 py-2 text-[12.5px] font-medium transition-colors [&_svg]:h-3.5 [&_svg]:w-3.5 [&_svg]:shrink-0',
                item.variant === 'danger'
                  ? 'text-[var(--err)] hover:bg-[var(--badge-err-bg)] [&_svg]:text-[var(--err)]'
                  : 'text-[var(--text)] hover:bg-[var(--surface)] [&_svg]:text-[var(--text-mute)]',
              )}
            >
              {item.icon}
              {item.label}
            </button>
          </div>
        ))}
      </div>
    </>,
    document.body,
  )
}

// ── Action bar ────────────────────────────────────────────────────────────────

export function EditorActionBar({ onRun, isRunning }: EditorActionBarProps) {
  const {
    btnRef, anchorRect,
    openMenu, closeMenu, openCopilot,
    exportWorkflow, autoLayout, deleteWorkflow, collapseRightPanel,
    isActive, isToggling, toggleActive,
  } = useEditorActionBar()
  const { id: workflowId } = useParams<{ id: string }>()
  const workflowName = useWorkflowEditorStore((s) => s.workflow?.name ?? '')
  const nodes = useWorkflowEditorStore((s) => s.nodes)
  const chatAppNode = nodes.find(n => n.type === 'trigger.chat_app')
  const hasChatAppTrigger = Boolean(chatAppNode)
  // Mirror the backend's slug fallback (app_slug → title → name) so the
  // URL chip appears even before the user sets an explicit slug.
  const chatAppSlug =
    (chatAppNode?.data?.properties?.app_slug as string) ||
    (chatAppNode?.data?.properties?.title as string) ||
    workflowName
  const wsSlug = useWorkspaceStore(s => s.currentWorkspace?.slug ?? '')
  const { toast } = useToast()

  // A chat-app graph runs when a visitor sends a message — a bare Run
  // with an empty trigger payload is meaningless. Route Run to the
  // hosted page instead (activating first if needed).
  const runViaChat = () => {
    if (!isActive) {
      toast('Activate first — a chat app runs when a visitor sends a message', { variant: 'warn' })
      return
    }
    window.open(`/apps/${wsSlug}/${slugifyAppUrl(chatAppSlug)}`, '_blank', 'noreferrer')
  }
  const [publishOpen, setPublishOpen] = useState(false)

  const menuItems: DropdownItem[] = [
    { label: 'Auto layout',        icon: <LayoutDashboard />, onClick: autoLayout },
    { label: 'Collapse panel',     icon: <PanelRightClose />, onClick: collapseRightPanel },
    { label: 'Lock workflow',      icon: <Lock />,            onClick: () => {}, dividerBefore: true },
    { label: 'Export workflow',    icon: <Download />,        onClick: exportWorkflow },
    { label: 'Duplicate workflow', icon: <Copy />,            onClick: () => {} },
    { label: 'Publish as template', icon: <Sparkles />,       onClick: () => setPublishOpen(true) },
    { label: 'Delete workflow',    icon: <Trash2 />,          onClick: deleteWorkflow, variant: 'danger', dividerBefore: true },
  ]

  return (
    <div className="shrink-0 border-b border-[var(--border-faint)]">
    <div className="flex items-center justify-between gap-2 px-3 py-2.5">
      <div className="flex items-center gap-1">
        <button
          ref={btnRef}
          onClick={openMenu}
          className={cn(
            'flex h-7 w-7 items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors',
            'hover:bg-[var(--surface)] hover:text-[var(--text)]',
            anchorRect && 'bg-[var(--surface)] text-[var(--text)]',
          )}
          title="Workflow options"
        >
          <MoreHorizontal className="h-4 w-4" />
        </button>

        <button
          onClick={openCopilot}
          className="flex h-7 w-7 items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
          title="Open Copilot"
        >
          <MessageCircle className="h-4 w-4" />
        </button>
      </div>

      <div className="flex items-center gap-2">
        {/* Share URL surfaces only when the graph has a chat_app trigger
            AND the workflow is active — mirrors how other triggers "just
            work" once the workflow is switched on. */}
        {hasChatAppTrigger && isActive && workflowId && (
          <ShareAppButton workflowId={workflowId} appSlug={chatAppSlug} />
        )}
        {/* Activate / Pause — toggles workflow.is_active. When active the
            cron / webhook triggers fire; pausing makes the runtime ignore
            them. Same control as the topbar's Active pill, surfaced here
            as a primary action next to Run. */}
        <Button
          variant={isActive ? 'outline' : 'secondary'}
          size="sm"
          onClick={toggleActive}
          disabled={isToggling}
          leftIcon={
            isToggling
              ? <Loader2 className="animate-spin" />
              : isActive
                ? <Power className="text-[var(--ok)]" />
                : <Rocket className="text-[var(--accent)]" />
          }
          title={isActive
            ? 'Workflow is live. Click to pause and ignore triggers.'
            : 'Activate the workflow so its triggers start firing.'}
        >
          {isToggling ? '…' : isActive ? 'Active' : 'Activate'}
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={hasChatAppTrigger ? runViaChat : onRun}
          disabled={isRunning}
          leftIcon={
            isRunning
              ? <Loader2 className="animate-spin" />
              : hasChatAppTrigger
                ? <MessageCircle />
                : <Play className="fill-current" />
          }
          title={hasChatAppTrigger
            ? 'Open the hosted chat page — the graph runs on each visitor message'
            : undefined}
        >
          {isRunning ? 'Running' : hasChatAppTrigger ? 'Open chat' : 'Run'}
        </Button>
      </div>

      {anchorRect && (
        <OptionsDropdown anchorRect={anchorRect} items={menuItems} onClose={closeMenu} />
      )}

      <PublishTemplateModal
        open={publishOpen}
        onClose={() => setPublishOpen(false)}
        workflowId={workflowId ?? null}
        defaultTitle={workflowName}
      />
    </div>
    </div>
  )
}

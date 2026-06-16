import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ChevronDown, Pencil, Activity, Check, MoreHorizontal, MessageCircle, Send, Play, Loader2,
  LayoutDashboard, Lock, Download, Copy, Trash2, PanelRightClose
} from 'lucide-react'
import { cn } from '@/lib/cn'
import { Dropdown, DropdownTrigger, DropdownContent, DropdownItem, Button } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { AppTopBarActions } from '@/shared/layouts/app-layout/app-top-bar-actions'
import type { AppLayoutController } from '@/shared/layouts/app-layout/use-app-layout-controller'
import { useEditorActionBar } from '../../hooks/useEditorActionBar'

interface EditorTopbarProps {
  controller: AppLayoutController
  workflowName: string
  isActive: boolean
  onToggleActive: () => void
  onRename: (name: string) => void
  onRun: () => void
  isRunning: boolean
  className?: string
}

export function EditorTopbar({
  controller,
  workflowName,
  isActive,
  onToggleActive,
  onRename,
  onRun,
  isRunning,
  className,
}: EditorTopbarProps) {
  const navigate = useNavigate()
  const [renaming, setRenaming] = useState(false)
  const [nameValue, setNameValue] = useState(workflowName)
  const [stateOpen, setStateOpen] = useState(false)

  const {
    openCopilot,
    exportWorkflow,
    autoLayout,
    deleteWorkflow,
    collapseRightPanel,
  } = useEditorActionBar()

  const handleRenameCommit = () => {
    const trimmed = nameValue.trim()
    if (trimmed && trimmed !== workflowName) onRename(trimmed)
    setRenaming(false)
  }

  return (
    <header
      data-role="editor-topbar"
      className={cn(
        'relative z-20 flex shrink-0 items-center justify-between gap-3 border-b border-[var(--border-faint)] bg-[var(--bg-2)] py-[8px] px-[22px]',
        className,
      )}
    >
      {/* ── Left ──────────────────────────────────────────── */}
      <div className="flex min-w-0 items-center gap-1.5">
        <button
          onClick={() => navigate(APP_ROUTES.AUTOMATIONS)}
          className="text-[12.5px] text-[var(--text-mute)] transition-colors hover:text-[var(--text)]"
        >
          Workflows
        </button>
        <span className="text-[11px] text-[var(--text-dim)]">/</span>

        {/* Workflow name + dropdown */}
        <Dropdown>
          <DropdownTrigger>
            <button className="flex h-8 max-w-[280px] items-center gap-1.5 rounded-[7px] px-2 py-1 text-[12.5px] font-medium text-[var(--text)] transition-colors hover:bg-[var(--surface)]">
              {renaming ? (
                <input
                  autoFocus
                  value={nameValue}
                  onChange={e => setNameValue(e.target.value)}
                  onBlur={handleRenameCommit}
                  onKeyDown={e => {
                    if (e.key === 'Enter') handleRenameCommit()
                    if (e.key === 'Escape') { setNameValue(workflowName); setRenaming(false) }
                    e.stopPropagation()
                  }}
                  onClick={e => e.stopPropagation()}
                  className="w-full bg-transparent outline-none"
                />
              ) : (
                <>
                  <span className="truncate">{workflowName}</span>
                  <ChevronDown className="h-3 w-3 shrink-0 text-[var(--text-faint)]" />
                </>
              )}
            </button>
          </DropdownTrigger>
          <DropdownContent className="w-56">
            <DropdownItem onClick={() => setRenaming(true)} leftIcon={<Pencil className="w-3.5 h-3.5" />}>
              Rename
            </DropdownItem>
            <DropdownItem onClick={() => navigate(APP_ROUTES.RUNS)} leftIcon={<Activity className="w-3.5 h-3.5" />}>
              View runs
            </DropdownItem>
          </DropdownContent>
        </Dropdown>

        {/* Active / Paused pill */}
        <Dropdown open={stateOpen} onOpenChange={setStateOpen}>
          <DropdownTrigger>
            <button
              className={cn(
                'flex items-center gap-1.5 rounded-[6px] border px-2 py-1 text-[11.5px] font-medium leading-none transition-colors',
                'border-[var(--border-faint)] bg-[var(--surface)] text-[var(--text)] hover:bg-[var(--surface-2)]',
              )}
            >
              <span
                className={cn('h-1.5 w-1.5 rounded-full', isActive ? 'bg-[var(--ok)]' : 'bg-[var(--warn)]')}
              />
              {isActive ? 'Active' : 'Paused'}
              <ChevronDown className="h-2.5 w-2.5 text-[var(--text-faint)]" />
            </button>
          </DropdownTrigger>
          <DropdownContent className="w-52">
            <button
              onClick={() => { if (!isActive) { onToggleActive(); } setStateOpen(false) }}
              className="flex w-full items-center gap-2.5 rounded-[7px] px-2.5 py-2 text-[12.5px] transition-colors hover:bg-[var(--surface)]"
            >
              <span className="h-2 w-2 rounded-full bg-[var(--ok)]" />
              <span className="flex-1 text-left">
                <span className="block font-medium">Active</span>
                <span className="text-[10.5px] text-[var(--text-faint)]">Triggers will fire</span>
              </span>
              {isActive && <Check className="h-3.5 w-3.5 text-[var(--text-mute)]" />}
            </button>
            <button
              onClick={() => { if (isActive) { onToggleActive(); } setStateOpen(false) }}
              className="flex w-full items-center gap-2.5 rounded-[7px] px-2.5 py-2 text-[12.5px] transition-colors hover:bg-[var(--surface)]"
            >
              <span className="h-2 w-2 rounded-full bg-[var(--warn)]" />
              <span className="flex-1 text-left">
                <span className="block font-medium">Paused</span>
                <span className="text-[10.5px] text-[var(--text-faint)]">Triggers ignored</span>
              </span>
              {!isActive && <Check className="h-3.5 w-3.5 text-[var(--text-mute)]" />}
            </button>
          </DropdownContent>
        </Dropdown>
      </div>

      {/* ── Right ─────────────────────────────────────────── */}
      <div className="flex items-center gap-4">
        {/* Editor Actions */}
        <div className="flex items-center gap-2 pr-4 border-r border-[var(--border-faint)]">
          <div className="flex items-center gap-1">
            <Dropdown>
              <DropdownTrigger>
                <button
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-[8px] text-[var(--text-mute)] transition-colors',
                    'hover:bg-[var(--surface)] hover:text-[var(--text)]',
                  )}
                  title="Workflow options"
                >
                  <MoreHorizontal className="h-4 w-4" />
                </button>
              </DropdownTrigger>
              <DropdownContent className="w-56">
                <DropdownItem onClick={autoLayout} leftIcon={<LayoutDashboard className="w-3.5 h-3.5" />}>
                  Auto layout
                </DropdownItem>
                <DropdownItem onClick={collapseRightPanel} leftIcon={<PanelRightClose className="w-3.5 h-3.5" />}>
                  Collapse panel
                </DropdownItem>
                <DropdownItem onClick={() => {}} leftIcon={<Lock className="w-3.5 h-3.5" />} className="border-t border-[var(--border-faint)] pt-2 mt-1">
                  Lock workflow
                </DropdownItem>
                <DropdownItem onClick={exportWorkflow} leftIcon={<Download className="w-3.5 h-3.5" />}>
                  Export workflow
                </DropdownItem>
                <DropdownItem onClick={() => {}} leftIcon={<Copy className="w-3.5 h-3.5" />}>
                  Duplicate workflow
                </DropdownItem>
                <DropdownItem onClick={deleteWorkflow} leftIcon={<Trash2 className="w-3.5 h-3.5 text-[var(--err)]" />} className="border-t border-[var(--border-faint)] pt-2 mt-1 text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.10)]">
                  Delete workflow
                </DropdownItem>
              </DropdownContent>
            </Dropdown>

            <button
              onClick={openCopilot}
              className="flex h-8 w-8 items-center justify-center rounded-[8px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
              title="Open Copilot"
            >
              <MessageCircle className="h-4 w-4" />
            </button>
          </div>

          <div className="flex items-center gap-2 ml-1">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Send className="text-[var(--accent)]" />}
              className="h-8 px-3 border-[var(--border-soft)] text-[var(--text)] bg-[var(--surface)] hover:bg-[var(--surface-2)] hover:border-[var(--border)]"
            >
              Deploy
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={onRun}
              disabled={isRunning}
              leftIcon={isRunning ? <Loader2 className="animate-spin" /> : <Play className="fill-current" />}
              className="h-8 px-4 bg-[var(--text)] text-[var(--bg)] border-none hover:opacity-90 active:scale-[0.97]"
            >
              {isRunning ? 'Running' : 'Run'}
            </Button>
          </div>
        </div>

        <AppTopBarActions controller={controller} />
      </div>
    </header>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronDown, Pencil, Activity, Check } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Dropdown, DropdownTrigger, DropdownContent, DropdownItem } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { AppTopBarActions } from '@/shared/layouts/app-layout/app-top-bar-actions'
import type { AppLayoutController } from '@/shared/layouts/app-layout/use-app-layout-controller'

interface EditorTopbarProps {
  controller: AppLayoutController
  workflowName: string
  isActive: boolean
  onToggleActive: () => void
  onRename: (name: string) => void
  className?: string
}

export function EditorTopbar({
  controller,
  workflowName,
  isActive,
  onToggleActive,
  onRename,
  className,
}: EditorTopbarProps) {
  const navigate = useNavigate()
  const [renaming, setRenaming] = useState(false)
  const [nameValue, setNameValue] = useState(workflowName)
  const [stateOpen, setStateOpen] = useState(false)

  const handleRenameCommit = () => {
    const trimmed = nameValue.trim()
    if (trimmed && trimmed !== workflowName) onRename(trimmed)
    setRenaming(false)
  }

  return (
    <header
      className={cn(
        'relative z-20 flex shrink-0 items-center justify-between gap-3 border-b border-[var(--border-faint)] bg-[var(--bg)] py-[8px] px-[22px]',
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
            <DropdownItem onClick={() => setRenaming(true)} leftIcon={<Pencil />}>
              Rename
            </DropdownItem>
            <DropdownItem onClick={() => navigate(APP_ROUTES.RUNS)} leftIcon={<Activity />}>
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
      <AppTopBarActions controller={controller} />
    </header>
  )
}

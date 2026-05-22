import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkspaceStore } from '../store/workspaceStore'
import { useCreateWorkspace, switchWorkspace } from '../hooks/useWorkspace'
import { cn } from '@/lib/cn'
import { Dropdown, DropdownTrigger, DropdownContent, DropdownItem, DropdownSeparator } from '@/shared/components'

export function WorkspaceSelector() {
  const navigate = useNavigate()
  const { currentWorkspace, currentWorkspaceId, workspaces } = useWorkspaceStore()
  const createWorkspace = useCreateWorkspace()

  const label = currentWorkspace?.name ?? 'Workspace'
  const initial = label[0]?.toUpperCase() ?? '?'
  const isPersonal = currentWorkspace?.is_personal ?? true

  const handleCreate = async () => {
    const name = window.prompt('New workspace name')
    if (!name?.trim()) return
    await createWorkspace.mutateAsync(name.trim())
  }

  const handleSwitch = (ws: typeof workspaces[number]) => {
    if (ws.id === currentWorkspaceId) return
    switchWorkspace(ws)
  }

  return (
    <Dropdown className="w-full">
      <DropdownTrigger className="w-full">
        <button className="flex items-center gap-[10px] py-[9px] px-[10px] w-full text-left bg-[var(--surface)] border border-[var(--border-faint)] rounded-[10px] cursor-pointer transition-colors duration-120 hover:bg-[var(--surface-2)] hover:border-[var(--border-soft)]" type="button">
          <span className="w-[26px] h-[26px] rounded-[7px] bg-[var(--text)] text-[var(--bg)] inline-flex items-center justify-center text-[11px] font-semibold tracking-tight shrink-0">{initial}</span>
          <span className="flex flex-col gap-[1px] min-w-0 flex-1">
            <span className="text-[13px] font-medium text-[var(--text)] whitespace-nowrap overflow-hidden text-ellipsis tracking-tight">{label}</span>
            <span className="text-[10.5px] text-[var(--text-faint)] font-mono tracking-widest uppercase">{isPersonal ? 'Personal' : 'Team workspace'}</span>
          </span>
          <Icons.Chevrons style={{ width: 13, height: 13, flexShrink: 0, color: 'var(--text-faint)' }} />
        </button>
      </DropdownTrigger>

      <DropdownContent className="w-[260px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[13px] p-[6px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in slide-in-from-top-1">
        {/* Current workspace header */}
        <div className="flex items-center gap-[10px] pt-[8px] px-[8px] pb-[10px]">
          <span className="w-[32px] h-[32px] rounded-[8px] bg-[var(--text)] text-[var(--bg)] inline-flex items-center justify-center text-[13px] font-bold shrink-0 tracking-tight">{initial}</span>
          <span className="flex flex-col gap-[2px] min-w-0">
            <span className="text-[13px] font-semibold text-[var(--text)] tracking-tight">{label}</span>
            <span className="text-[10.5px] font-mono text-[var(--text-faint)] tracking-widest uppercase">
              {workspaces.find(w => w.id === currentWorkspaceId)?.role ?? 'member'}
            </span>
          </span>
        </div>

        <DropdownSeparator className="bg-[var(--border-faint)] my-[4px]" />

        {/* All workspaces */}
        <div className="flex flex-col gap-[1px] py-[4px] px-0">
          <span className="text-[10px] font-mono text-[var(--text-dim)] tracking-widest uppercase pt-[4px] px-[10px] pb-[6px]">Workspaces</span>
          {workspaces.map(ws => (
            <DropdownItem
              key={ws.id}
              className={cn(
                "flex items-center gap-[9px] py-[7px] px-[10px] rounded-[8px] w-full text-left text-[13px] font-medium text-[var(--text-mute)] bg-transparent border-none cursor-pointer transition-colors duration-80 hover:bg-[var(--surface)] hover:text-[var(--text)]",
                ws.id === currentWorkspaceId && "text-[var(--text)] bg-[var(--surface)]"
              )}
              onClick={() => handleSwitch(ws)}
            >
              <span className="w-[22px] h-[22px] rounded-[6px] bg-[var(--surface-3)] border border-[var(--border-soft)] inline-flex items-center justify-center text-[10px] font-bold text-[var(--text)] shrink-0">{ws.name[0]?.toUpperCase()}</span>
              <span className="flex-1 min-w-0 overflow-hidden text-ellipsis whitespace-nowrap">{ws.name}</span>
              {ws.id === currentWorkspaceId && (
                <Icons.Check style={{ width: 12, height: 12, color: 'var(--ok)', flexShrink: 0 }} />
              )}
            </DropdownItem>
          ))}
          <DropdownItem
            className="flex items-center gap-[8px] py-[7px] px-[10px] rounded-[8px] w-full text-left text-[12.5px] font-medium text-[var(--text-faint)] bg-transparent border-none cursor-pointer transition-colors duration-80 hover:bg-[var(--surface)] hover:text-[var(--text)] disabled:opacity-50 disabled:cursor-default"
            onClick={handleCreate}
            disabled={createWorkspace.isPending}
          >
            <Icons.Plus style={{ width: 12, height: 12 }} />
            {createWorkspace.isPending ? 'Creating…' : 'New workspace'}
          </DropdownItem>
        </div>

        <DropdownSeparator className="bg-[var(--border-faint)] my-[4px]" />

        {/* Settings shortcut */}
        <DropdownItem
          className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[8px] w-full text-left text-[13px] font-medium text-[var(--text-mute)] bg-transparent border-none cursor-pointer transition-colors duration-80 hover:bg-[var(--surface)] hover:text-[var(--text)]"
          onClick={() => navigate(APP_ROUTES.WORKSPACE_SETTINGS)}
        >
          <Icons.Users style={{ width: 13, height: 13, color: 'var(--text-faint)' }} />
          Manage members
        </DropdownItem>
      </DropdownContent>
    </Dropdown>
  )
}

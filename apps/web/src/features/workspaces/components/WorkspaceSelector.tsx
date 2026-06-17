import { useState, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkspaceStore } from '../store/workspaceStore'
import { useCreateWorkspace, switchWorkspace } from '../hooks/useWorkspace'
import { cn } from '@/lib/cn'
import { useToast } from '@/shared/components'

export function WorkspaceSelector() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { currentWorkspace, currentWorkspaceId, workspaces } = useWorkspaceStore()
  const createWorkspace = useCreateWorkspace()

  const [open, setOpen] = useState(false)
  const [pos, setPos]   = useState<{ top: number; left: number; width: number } | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName]       = useState('')
  const triggerRef = useRef<HTMLButtonElement>(null)

  const label    = currentWorkspace?.name ?? 'Workspace'
  const initial  = label[0]?.toUpperCase() ?? '?'
  const isPersonal = currentWorkspace?.is_personal ?? true

  const openDropdown = () => {
    const rect = triggerRef.current?.getBoundingClientRect()
    if (rect) setPos({ top: rect.bottom + 6, left: rect.left, width: rect.width })
    setOpen(true)
  }

  const close = () => { setOpen(false); setShowCreate(false); setNewName('') }

  const handleSwitch = (ws: typeof workspaces[number]) => {
    if (ws.id !== currentWorkspaceId) switchWorkspace(ws)
    close()
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    try {
      await createWorkspace.mutateAsync(newName.trim())
      toast('Workspace created', { variant: 'ok', description: newName.trim() })
      close()
    } catch (err) {
      toast('Failed', { variant: 'err', description: err instanceof Error ? err.message : 'Try again.' })
    }
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={openDropdown}
        className="flex items-center gap-[9px] py-[7px] px-[8px] w-full text-left bg-[rgba(255,255,255,0.02)] border border-[var(--border-soft)] rounded-[8px] cursor-pointer transition-all duration-120 hover:bg-[rgba(255,255,255,0.05)] hover:border-[var(--border)] group-data-[collapsed=true]/shell:p-0 group-data-[collapsed=true]/shell:w-[36px] group-data-[collapsed=true]/shell:h-[36px] group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:mx-auto group-data-[collapsed=true]/shell:rounded-full"
      >
        <span className="w-[24px] h-[24px] rounded-[6px] inline-flex items-center justify-center text-[12px] font-semibold text-[var(--text)] shrink-0 bg-[linear-gradient(135deg,var(--surface-3),var(--surface))] group-data-[collapsed=true]/shell:w-[28px] group-data-[collapsed=true]/shell:h-[28px] group-data-[collapsed=true]/shell:rounded-full transition-all duration-200">{initial}</span>
        <span className="flex flex-col gap-0 min-w-0 flex-1 group-data-[collapsed=true]/shell:hidden leading-tight">
          <span className="text-[13px] font-medium text-[var(--text)] whitespace-nowrap overflow-hidden text-ellipsis tracking-tight">{label}</span>
          <span className="text-[10px] text-[var(--text-faint)] font-semibold tracking-[0.06em] uppercase">{isPersonal ? 'Personal' : 'Team'}</span>
        </span>
        <Icons.Chevrons style={{ width: 13, height: 13, flexShrink: 0, color: 'var(--text-faint)' }} className="group-data-[collapsed=true]/shell:hidden" />
      </button>

      {open && pos && createPortal(
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-[9998]" onClick={close} />

          {/* Dropdown */}
          <div
            className="fixed z-[9999] bg-[var(--bg-2)] border border-[var(--border)] rounded-[13px] p-[6px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]"
            style={{ top: pos.top, left: pos.left, width: Math.max(pos.width, 260) }}
          >
            {/* Current workspace header */}
            <div className="flex items-center gap-[10px] pt-[8px] px-[8px] pb-[10px]">
              <span className="w-[32px] h-[32px] rounded-[8px] bg-[var(--text)] text-[var(--bg)] inline-flex items-center justify-center text-[13px] font-bold shrink-0 tracking-tight">{initial}</span>
              <span className="flex flex-col gap-[2px] min-w-0">
                <span className="text-[13px] font-semibold text-[var(--text)] tracking-tight truncate">{label}</span>
                <span className="text-[10.5px] font-mono text-[var(--text-faint)] tracking-widest uppercase">
                  {workspaces.find(w => w.id === currentWorkspaceId)?.role ?? 'member'}
                </span>
              </span>
            </div>

            <div className="h-px bg-[var(--border-faint)] my-1" />

            {/* Workspace list */}
            <div className="flex flex-col gap-[1px] py-1">
              <span className="text-[10px] font-mono text-[var(--text-dim)] tracking-widest uppercase px-[10px] py-[4px]">Workspaces</span>
              {workspaces.map(ws => (
                <button
                  key={ws.id}
                  onClick={() => handleSwitch(ws)}
                  className={cn(
                    'flex items-center gap-[9px] py-[7px] px-[10px] rounded-[8px] w-full text-left text-[13px] font-medium text-[var(--text-mute)] bg-transparent border-none cursor-pointer transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]',
                    ws.id === currentWorkspaceId && 'text-[var(--text)] bg-[var(--surface)]'
                  )}
                >
                  <span className="w-[22px] h-[22px] rounded-[6px] bg-[var(--surface-3)] border border-[var(--border-soft)] inline-flex items-center justify-center text-[10px] font-bold text-[var(--text)] shrink-0">
                    {ws.name[0]?.toUpperCase()}
                  </span>
                  <span className="flex-1 min-w-0 truncate">{ws.name}</span>
                  {ws.id === currentWorkspaceId && (
                    <Icons.Check style={{ width: 12, height: 12, color: 'var(--ok)', flexShrink: 0 }} />
                  )}
                </button>
              ))}

              {/* Create new workspace */}
              {!showCreate ? (
                <button
                  onClick={() => setShowCreate(true)}
                  className="flex items-center gap-[8px] py-[7px] px-[10px] rounded-[8px] w-full text-left text-[12.5px] font-medium text-[var(--text-faint)] bg-transparent border-none cursor-pointer transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
                >
                  <Icons.Plus style={{ width: 12, height: 12 }} />
                  New workspace
                </button>
              ) : (
                <form onSubmit={handleCreate} className="flex items-center gap-2 px-[10px] py-[6px]">
                  <input
                    autoFocus
                    type="text"
                    value={newName}
                    onChange={e => setNewName(e.target.value)}
                    placeholder="Workspace name"
                    onKeyDown={e => e.key === 'Escape' && setShowCreate(false)}
                    className="flex-1 h-[30px] px-2 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[7px] text-[12.5px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors"
                  />
                  <button
                    type="submit"
                    disabled={!newName.trim() || createWorkspace.isPending}
                    className="h-[30px] px-2.5 rounded-[7px] bg-[var(--text)] text-[var(--bg)] text-[12px] font-medium border-none cursor-pointer disabled:opacity-40"
                  >
                    {createWorkspace.isPending ? '…' : 'Create'}
                  </button>
                </form>
              )}
            </div>

            <div className="h-px bg-[var(--border-faint)] my-1" />

            {/* Settings */}
            <button
              onClick={() => { close(); navigate(APP_ROUTES.WORKSPACE_SETTINGS) }}
              className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[8px] w-full text-left text-[13px] font-medium text-[var(--text-mute)] bg-transparent border-none cursor-pointer transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
            >
              <Icons.Users style={{ width: 13, height: 13, color: 'var(--text-faint)' }} />
              Manage members
            </button>
          </div>
        </>,
        document.body
      )}
    </>
  )
}

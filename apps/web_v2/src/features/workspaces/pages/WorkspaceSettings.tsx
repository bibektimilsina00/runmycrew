import { Icons } from '@/shared/components/icons'
import { useWorkspaces, useWorkspaceMembers } from '../hooks/useWorkspace'
import { useWorkspaceStore } from '../store/workspaceStore'
import { MemberList } from '../components/MemberList'
import { InviteForm } from '../components/InviteForm'
import { cn } from '@/lib/cn'

export function WorkspaceSettings() {
  useWorkspaces() // keep workspace list fresh
  const currentWorkspace = useWorkspaceStore(s => s.currentWorkspace)
  const currentWorkspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const canManage = useWorkspaceStore(s => s.canManageMembers())
  const currentRole = useWorkspaceStore(s => s.currentRole)
  const { data: members = [], isLoading } = useWorkspaceMembers(currentWorkspaceId)

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace settings</span>
          <h1>{currentWorkspace?.name ?? 'Workspace'}</h1>
        </div>
      </div>

      {/* Info strip */}
      <div className="flex items-center flex-wrap bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] p-0 overflow-hidden">
        <div className="flex flex-col gap-[3px] py-[14px] px-[20px] flex-1">
          <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)]">Plan</span>
          <span className="text-[13.5px] font-medium text-[var(--text)]">{currentWorkspace?.plan ?? '—'}</span>
        </div>
        <div className="w-[1px] h-[40px] bg-[var(--border-faint)] shrink-0" />
        <div className="flex flex-col gap-[3px] py-[14px] px-[20px] flex-1">
          <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)]">Your role</span>
          <span className={cn(
            "text-[13.5px] font-medium",
            currentRole === 'owner' ? 'text-[var(--ok)]' :
            currentRole === 'admin' ? 'text-[var(--accent)]' :
            currentRole === 'member' ? 'text-[var(--text-mute)]' :
            currentRole === 'viewer' ? 'text-[var(--text-dim)]' :
            'text-[var(--text)]'
          )}>
            {currentRole ?? '—'}
          </span>
        </div>
        <div className="w-[1px] h-[40px] bg-[var(--border-faint)] shrink-0" />
        <div className="flex flex-col gap-[3px] py-[14px] px-[20px] flex-1">
          <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)]">Members</span>
          <span className="text-[13.5px] font-medium text-[var(--text)]">{members.length}</span>
        </div>
        <div className="w-[1px] h-[40px] bg-[var(--border-faint)] shrink-0" />
        <div className="flex flex-col gap-[3px] py-[14px] px-[20px] flex-1">
          <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)]">Workspace ID</span>
          <span className="text-[13.5px] font-medium text-[var(--text)] font-mono text-[12px] tracking-tight">
            {currentWorkspace?.slug ?? '—'}
          </span>
        </div>
      </div>

      {/* Members */}
      <section className="flex flex-col gap-[14px]">
        <div className="flex items-center gap-[10px]">
          <div className="flex items-center gap-[8px] text-[14px] font-semibold text-[var(--text)] tracking-tight">
            <Icons.Users className="text-[var(--text-faint)] w-[14px] h-[14px]" />
            Members
          </div>
          <span className="text-[11px] font-mono text-[var(--text-faint)] bg-[var(--surface)] border border-[var(--border-faint)] py-[2px] px-[7px] pb-[1px] rounded-[4px]">
            {members.length}
          </span>
        </div>
        {isLoading ? (
          <div className="text-[13px] text-[var(--text-faint)] py-[16px]">Loading members…</div>
        ) : (
          <MemberList members={members} workspaceId={currentWorkspaceId ?? ''} />
        )}
      </section>

      {/* Invite — only admins/owners */}
      {canManage && (
        <section className="flex flex-col gap-[14px]">
          <div className="flex items-center gap-[10px]">
            <div className="flex items-center gap-[8px] text-[14px] font-semibold text-[var(--text)] tracking-tight">
              <Icons.Plus className="text-[var(--text-faint)] w-[14px] h-[14px]" />
              Invite people
            </div>
          </div>
          <InviteForm />
        </section>
      )}
    </div>
  )
}

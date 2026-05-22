import { useWorkspaceStore } from '../store/workspaceStore'
import { useUpdateMember, useRemoveMember } from '../hooks/useWorkspace'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { RoleSelect } from './RoleSelect'
import type { WorkspaceMember, WorkspaceRole } from '../types/workspaceTypes'
import { cn } from '@/lib/cn'

const EDITABLE_ROLES: WorkspaceRole[] = ['admin', 'member', 'viewer']

interface Props {
  members: WorkspaceMember[]
  workspaceId: string
}

export function MemberList({ members, workspaceId }: Props) {
  const { user } = useAuth()
  const canManage = useWorkspaceStore(s => s.canManageMembers())
  const updateMember = useUpdateMember(workspaceId)
  const removeMember = useRemoveMember(workspaceId)

  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden">
      <div className="grid grid-cols-[minmax(0,1fr)_120px_120px_40px] gap-[12px] px-[16px] py-[9px] border-b border-[var(--border-faint)] font-mono text-[10.5px] tracking-widest uppercase text-[var(--text-dim)] bg-[var(--surface)]">
        <span>Member</span>
        <span>Role</span>
        <span>Joined</span>
        <span></span>
      </div>
      {members.map(m => {
        const displayName = m.user.full_name || m.user.email
        const initial = displayName[0]?.toUpperCase() ?? '?'
        const isCurrentUser = m.user_id === user?.id
        const isOwner = m.role === 'owner'
        const joinedDate = new Date(m.joined_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

        return (
          <div key={m.id} className="grid grid-cols-[minmax(0,1fr)_120px_120px_40px] gap-[12px] px-[16px] py-[12px] items-center border-b border-[var(--border-faint)] transition-colors duration-80 last:border-none hover:bg-[var(--surface)]">
            <div className="flex items-center gap-[10px] min-w-0">
              <span className="w-[28px] h-[28px] rounded-[8px] bg-[var(--surface-3)] border border-[var(--border-soft)] inline-flex items-center justify-center text-[11px] font-semibold text-[var(--text)] shrink-0">{initial}</span>
              <span className="flex flex-col gap-[1px] min-w-0">
                <span className="text-[13px] font-medium text-[var(--text)] inline-flex items-center gap-[6px] whitespace-nowrap overflow-hidden text-ellipsis">
                  {displayName}
                  {isCurrentUser && <span className="text-[9.5px] font-mono font-semibold tracking-widest uppercase text-[var(--accent)] bg-[oklch(0.78_0.13_245/0.14)] py-[2px] px-[6px] pb-[1px] rounded-[4px]">you</span>}
                </span>
                <span className="text-[11px] text-[var(--text-faint)] font-mono">{m.user.email}</span>
              </span>
            </div>

            <div className="flex items-center">
              {canManage && !isOwner ? (
                <RoleSelect
                  value={m.role}
                  options={EDITABLE_ROLES}
                  onChange={role => updateMember.mutate({ userId: m.user_id, role })}
                  disabled={updateMember.isPending}
                />
              ) : (
                <span className={cn(
                  "font-mono text-[10px] tracking-widest uppercase py-[3px] px-[8px] pb-[2px] rounded-[5px] font-medium",
                  m.role === 'owner' && "bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]",
                  m.role === 'admin' && "bg-[oklch(0.78_0.13_245/0.14)] text-[var(--accent)]",
                  m.role === 'member' && "bg-[var(--surface-2)] text-[var(--text-mute)]",
                  m.role === 'viewer' && "bg-[var(--surface)] text-[var(--text-dim)]"
                )}>{m.role}</span>
              )}
            </div>

            <span className="text-[12px] text-[var(--text-faint)] font-mono">{joinedDate}</span>

            <div className="flex items-center justify-end">
              {canManage && !isOwner && !isCurrentUser && (
                <button
                  className="w-[24px] h-[24px] rounded-[6px] inline-flex items-center justify-center bg-transparent border-none cursor-pointer text-[10px] text-[var(--text-dim)] transition-colors duration-80 hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)]"
                  title="Remove member"
                  onClick={() => {
                    if (confirm(`Remove ${displayName} from this workspace?`)) {
                      removeMember.mutate(m.user_id)
                    }
                  }}
                >
                  ✕
                </button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

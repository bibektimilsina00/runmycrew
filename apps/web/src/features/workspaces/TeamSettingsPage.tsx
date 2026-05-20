import React from 'react'
import { Copy, Mail, Users, Trash2 } from 'lucide-react'
import {
  useCreateWorkspaceInvite,
  useUpdateWorkspaceMember,
  useRemoveWorkspaceMember,
  useWorkspaceMembers,
  useWorkspaces,
} from '@/features/workspaces/hooks'
import type { WorkspaceRole } from '@/lib/api/contracts'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { useAuthStore } from '@/stores/auth-store'

const ROLES: WorkspaceRole[] = ['owner', 'admin', 'member', 'viewer']

export function TeamSettingsPage() {
  useWorkspaces()
  const currentWorkspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const currentWorkspace = useWorkspaceStore(s => s.currentWorkspace)
  const canManageMembers = useWorkspaceStore(s => s.canManageMembers())
  const { data: members = [] } = useWorkspaceMembers(currentWorkspaceId)
  const currentUser = useAuthStore(s => s.user)
  const invite = useCreateWorkspaceInvite(currentWorkspaceId)
  const updateMember = useUpdateWorkspaceMember(currentWorkspaceId)
  const removeMember = useRemoveWorkspaceMember(currentWorkspaceId)
  const [email, setEmail] = React.useState('')
  const [role, setRole] = React.useState<WorkspaceRole>('member')
  const [sendEmail, setSendEmail] = React.useState(true)

  const submitInvite = (event: React.FormEvent) => {
    event.preventDefault()
    invite.mutate({ email, role, send_email: sendEmail })
  }

  return (
    <div className="h-full overflow-auto bg-[var(--bg)] p-6 text-white">
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <p className="text-[12px] uppercase text-[var(--text-muted)]">Workspace</p>
          <h1 className="text-2xl font-semibold">{currentWorkspace?.name ?? 'Team'}</h1>
        </div>

        <section className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Users className="h-4 w-4" />
            Members
          </div>
          <div className="overflow-hidden rounded-lg border border-[var(--border-default)]">
            {members.map(member => (
              <div key={member.id} className="flex items-center gap-3 border-b border-[var(--border-default)] px-4 py-3 last:border-b-0">
                <div className="flex h-8 w-8 items-center justify-center rounded bg-[var(--surface-3)] text-xs font-semibold">
                  {(member.user.full_name ?? member.user.email)[0]?.toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm">{member.user.full_name ?? member.user.email}</p>
                  <p className="truncate text-xs text-[var(--text-muted)]">{member.user.email}</p>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={member.role}
                    disabled={!canManageMembers || member.role === 'owner'}
                    onChange={event => updateMember.mutate({ userId: member.user_id, role: event.target.value as WorkspaceRole })}
                    className="rounded border border-[var(--border-default)] bg-[var(--surface-2)] px-2 py-1 text-xs"
                  >
                    {ROLES.map(option => <option key={option} value={option}>{option}</option>)}
                  </select>
                  {canManageMembers && member.role !== 'owner' && member.user_id !== currentUser?.id && (
                    <button
                      onClick={() => {
                        if (confirm(`Remove ${member.user.full_name ?? member.user.email} from workspace?`)) {
                          removeMember.mutate(member.user_id)
                        }
                      }}
                      className="rounded p-1 text-[var(--text-muted)] hover:bg-red-500/10 hover:text-red-400 transition-colors"
                      title="Remove member"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {canManageMembers && (
          <section className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Mail className="h-4 w-4" />
              Invite
            </div>
            <form onSubmit={submitInvite} className="grid gap-3 rounded-lg border border-[var(--border-default)] p-4 md:grid-cols-[1fr_140px_auto]">
              <input
                value={email}
                onChange={event => setEmail(event.target.value)}
                placeholder="teammate@example.com"
                type="email"
                required
                className="rounded border border-[var(--border-default)] bg-[var(--surface-2)] px-3 py-2 text-sm"
              />
              <select value={role} onChange={event => setRole(event.target.value as WorkspaceRole)} className="rounded border border-[var(--border-default)] bg-[var(--surface-2)] px-3 py-2 text-sm">
                {ROLES.filter(option => option !== 'owner').map(option => <option key={option} value={option}>{option}</option>)}
              </select>
              <button className="rounded bg-white px-4 py-2 text-sm font-medium text-black" type="submit">
                Invite
              </button>
              <label className="flex items-center gap-2 text-xs text-[var(--text-muted)] md:col-span-3">
                <input type="checkbox" checked={sendEmail} onChange={event => setSendEmail(event.target.checked)} />
                Send email and generate invite link
              </label>
            </form>
            {invite.data && (
              <div className="flex items-center gap-2 rounded-lg border border-[var(--border-default)] bg-[var(--surface-2)] p-3 text-sm">
                <span className="min-w-0 flex-1 truncate">{invite.data.invite_url}</span>
                <button
                  className="rounded p-1 hover:bg-[var(--surface-hover)]"
                  onClick={() => navigator.clipboard.writeText(invite.data.invite_url)}
                  title="Copy invite link"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  )
}

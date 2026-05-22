import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useToast } from '@/shared/components'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useWorkspaces, useWorkspaceMembers, useRemoveMember, useUpdateWorkspace, useDeleteWorkspace } from '../hooks/useWorkspace'
import { useWorkspaceStore } from '../store/workspaceStore'
import { MemberList } from '../components/MemberList'
import { InviteForm } from '../components/InviteForm'

type Tab = 'members' | 'general' | 'danger'

export function WorkspaceSettings() {
  useWorkspaces()
  const { user } = useAuth()
  const { toast } = useToast()
  const currentWorkspace = useWorkspaceStore(s => s.currentWorkspace)
  const currentWorkspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const currentRole = useWorkspaceStore(s => s.currentRole)
  const canManage = useWorkspaceStore(s => s.canManageMembers())
  const isOwner = useWorkspaceStore(s => s.isOwner())

  const { data: members = [], isLoading } = useWorkspaceMembers(currentWorkspaceId)
  const removeMember = useRemoveMember(currentWorkspaceId)
  const updateWorkspace = useUpdateWorkspace()
  const deleteWorkspace = useDeleteWorkspace()
  const navigate = useNavigate()

  const [tab, setTab] = useState<Tab>('members')
  const [memberSearch, setMemberSearch] = useState('')
  const [memberRoleFilter, setMemberRoleFilter] = useState<string>('all')
  const [leavePending, setLeavePending] = useState(false)
  const [leaveConfirmOpen, setLeaveConfirmOpen] = useState(false)

  // Rename state
  const [renameName, setRenameName] = useState(currentWorkspace?.name ?? '')
  const [renameError, setRenameError] = useState<string | null>(null)

  // Delete state
  const [deleteConfirmName, setDeleteConfirmName] = useState('')
  const [deleteOpen, setDeleteOpen] = useState(false)

  const initial = (currentWorkspace?.name || '?')[0].toUpperCase()

  // Filter members
  const filteredMembers = useMemo(() => {
    let list = members
    if (memberSearch.trim()) {
      const q = memberSearch.toLowerCase()
      list = list.filter(m =>
        (m.user.full_name || '').toLowerCase().includes(q) ||
        m.user.email.toLowerCase().includes(q)
      )
    }
    if (memberRoleFilter !== 'all') {
      list = list.filter(m => m.role === memberRoleFilter)
    }
    return list
  }, [members, memberSearch, memberRoleFilter])

  const roleCounts = useMemo(() => ({
    all: members.length,
    owner: members.filter(m => m.role === 'owner').length,
    admin: members.filter(m => m.role === 'admin').length,
    member: members.filter(m => m.role === 'member').length,
    viewer: members.filter(m => m.role === 'viewer').length,
  }), [members])

  const handleLeave = async () => {
    if (!user?.id || !currentWorkspaceId) return
    setLeavePending(true)
    try {
      await removeMember.mutateAsync(user.id)
      toast('Left workspace', { variant: 'ok', description: `You left ${currentWorkspace?.name}.` })
      // workspace store will auto-select next workspace
      setLeaveConfirmOpen(false)
    } catch (err) {
      toast('Failed to leave', { variant: 'err', description: err instanceof Error ? err.message : 'Try again.' })
    } finally {
      setLeavePending(false)
    }
  }

  const handleRename = async () => {
    const trimmed = renameName.trim()
    if (!trimmed) { setRenameError('Name cannot be empty.'); return }
    if (trimmed === currentWorkspace?.name) { setRenameError('That\'s already the current name.'); return }
    setRenameError(null)
    try {
      await updateWorkspace.mutateAsync({ workspaceId: currentWorkspaceId!, name: trimmed })
      toast('Workspace renamed', { variant: 'ok', description: `Now called "${trimmed}".` })
    } catch (err) {
      setRenameError(err instanceof Error ? err.message : 'Failed to rename.')
    }
  }

  const handleDelete = async () => {
    if (deleteConfirmName !== currentWorkspace?.name) return
    try {
      await deleteWorkspace.mutateAsync(currentWorkspaceId!)
      toast('Workspace deleted', { variant: 'ok' })
      navigate(APP_ROUTES.DASHBOARD)
    } catch (err) {
      toast('Failed to delete', { variant: 'err', description: err instanceof Error ? err.message : 'Try again.' })
    }
  }

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'members', label: 'Members', icon: <Icons.Users className="w-[13px] h-[13px]" /> },
    { id: 'general', label: 'General', icon: <Icons.Settings className="w-[13px] h-[13px]" /> },
    { id: 'danger', label: 'Danger zone', icon: <Icons.Activity className="w-[13px] h-[13px]" /> },
  ]

  return (
    <div className="view-body">
      {/* Hero header */}
      <div className="flex items-start gap-5">
        <div className="w-[56px] h-[56px] rounded-[14px] bg-[var(--text)] text-[var(--bg)] flex items-center justify-center text-[22px] font-bold shrink-0">
          {initial}
        </div>
        <div className="flex flex-col gap-1.5 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-[22px] font-semibold text-[var(--text)] tracking-tight m-0 leading-none">
              {currentWorkspace?.name ?? 'Workspace'}
            </h1>
            <span className={[
              'font-mono text-[9.5px] font-semibold tracking-widest uppercase px-[8px] py-[3px] rounded-[5px]',
              isOwner ? 'bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]' :
              currentRole === 'admin' ? 'bg-[oklch(0.78_0.13_245/0.14)] text-[var(--accent)]' :
              'bg-[var(--surface-2)] text-[var(--text-mute)]'
            ].join(' ')}>
              {currentRole ?? 'member'}
            </span>
          </div>
          <div className="flex items-center gap-4 text-[12px] font-mono text-[var(--text-faint)]">
            <span className="flex items-center gap-1.5">
              <Icons.Users className="w-[11px] h-[11px]" />
              {members.length} {members.length === 1 ? 'member' : 'members'}
            </span>
            <span>·</span>
            <span>{currentWorkspace?.plan ?? 'free'} plan</span>
            <span>·</span>
            <span className="lowercase">{currentWorkspace?.slug ?? ''}</span>
          </div>
        </div>
      </div>

      {/* Tab nav */}
      <div className="flex items-center gap-1 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] p-[3px] w-fit">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={[
              'inline-flex items-center gap-[6px] px-[12px] py-[6px] rounded-[6px] text-[12.5px] font-medium transition-colors duration-80',
              tab === t.id
                ? 'bg-[var(--surface)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]'
                : 'text-[var(--text-mute)] hover:text-[var(--text)]',
              t.id === 'danger' && tab !== 'danger' ? 'hover:text-[var(--err)]' : '',
            ].join(' ')}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Members tab ── */}
      {tab === 'members' && (
        <div className="flex flex-col gap-6">
          {/* Filter bar */}
          <div className="flex items-center gap-3 flex-wrap">
            {/* Role filter tabs */}
            <div className="flex items-center bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] p-[3px] gap-[2px]">
              {(['all', 'owner', 'admin', 'member', 'viewer'] as const).map(r => (
                roleCounts[r] > 0 || r === 'all' ? (
                  <button
                    key={r}
                    onClick={() => setMemberRoleFilter(r)}
                    className={[
                      'inline-flex items-center gap-[6px] px-[10px] py-[5px] rounded-[6px] text-[12px] font-medium capitalize transition-colors duration-80',
                      memberRoleFilter === r
                        ? 'bg-[var(--surface)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]'
                        : 'text-[var(--text-mute)] hover:text-[var(--text)]',
                    ].join(' ')}
                  >
                    {r === 'all' ? 'All' : r}
                    <span className="font-mono text-[10px] text-[var(--text-faint)] bg-[var(--surface)] border border-[var(--border-faint)] px-[5px] py-[1px] rounded-[3px]">
                      {roleCounts[r]}
                    </span>
                  </button>
                ) : null
              ))}
            </div>

            {/* Search */}
            <div className="flex items-center gap-2 flex-1 max-w-[280px] h-[34px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] focus-within:border-[var(--border)] transition-colors">
              <Icons.Search className="w-[13px] h-[13px] text-[var(--text-faint)] shrink-0" />
              <input
                type="text"
                placeholder="Search members"
                value={memberSearch}
                onChange={e => setMemberSearch(e.target.value)}
                className="flex-1 bg-transparent border-none outline-none text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)]"
              />
              {memberSearch && (
                <button onClick={() => setMemberSearch('')} className="text-[var(--text-faint)] hover:text-[var(--text)] text-[12px]">✕</button>
              )}
            </div>
          </div>

          {/* Member list */}
          {isLoading ? (
            <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
              <div className="w-[16px] h-[16px] border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
              Loading members…
            </div>
          ) : filteredMembers.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-[var(--text-faint)]">
              <Icons.Users className="w-[20px] h-[20px] text-[var(--text-dim)]" />
              <span className="text-[13px]">
                {memberSearch ? 'No members match your search.' : 'No members found.'}
              </span>
            </div>
          ) : (
            <MemberList members={filteredMembers} workspaceId={currentWorkspaceId ?? ''} />
          )}

          {/* Invite section — admins + owners only */}
          {canManage && (
            <div className="flex flex-col gap-4">
              <div className="h-px bg-[var(--border-faint)]" />
              <div className="flex items-center gap-2 text-[14px] font-semibold text-[var(--text)] tracking-tight">
                <Icons.Plus className="w-[14px] h-[14px] text-[var(--text-faint)]" />
                Invite people
              </div>
              <InviteForm />
            </div>
          )}
        </div>
      )}

      {/* ── General tab ── */}
      {tab === 'general' && (
        <div className="flex flex-col gap-5">
          {/* Info grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Plan', value: currentWorkspace?.plan ?? '—' },
              { label: 'Your role', value: currentRole ?? '—', colored: true },
              { label: 'Members', value: String(members.length) },
              { label: 'Slug', value: currentWorkspace?.slug ?? '—', mono: true },
            ].map(item => (
              <div key={item.label} className="flex flex-col gap-1.5 px-4 py-3.5 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px]">
                <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)]">{item.label}</span>
                <span className={[
                  'text-[14px] font-medium',
                  item.mono ? 'font-mono text-[12px] text-[var(--text-mute)]' : 'text-[var(--text)]',
                  item.colored && currentRole === 'owner' ? 'text-[var(--ok)]' :
                  item.colored && currentRole === 'admin' ? 'text-[var(--accent)]' : '',
                ].join(' ')}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>

          {/* Rename workspace — owner only */}
          <div className="flex flex-col gap-3 p-5 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px]">
            <div>
              <div className="text-[13.5px] font-semibold text-[var(--text)]">Workspace name</div>
              <p className="text-[12px] text-[var(--text-faint)] mt-0.5">The display name shown across the app.</p>
            </div>
            <div className="flex items-center gap-3 max-w-md">
              <div className={[
                'flex items-center gap-2.5 px-3 h-[38px] flex-1 border rounded-[9px] transition-colors',
                isOwner
                  ? 'bg-[var(--bg-2)] border-[var(--border-faint)] focus-within:border-[var(--border)]'
                  : 'bg-[var(--surface)] border-[var(--border-faint)] opacity-60 cursor-not-allowed',
              ].join(' ')}>
                <Icons.Folder className="w-[14px] h-[14px] text-[var(--text-faint)] shrink-0" />
                <input
                  type="text"
                  value={renameName}
                  onChange={e => { setRenameName(e.target.value); setRenameError(null) }}
                  onKeyDown={e => e.key === 'Enter' && isOwner && handleRename()}
                  disabled={!isOwner}
                  className="flex-1 bg-transparent border-none outline-none text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] disabled:cursor-not-allowed"
                />
              </div>
              {isOwner && (
                <button
                  onClick={handleRename}
                  disabled={updateWorkspace.isPending || renameName.trim() === currentWorkspace?.name}
                  className="inline-flex items-center gap-2 px-4 h-[38px] rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer shrink-0 hover:bg-[oklch(0.90_0.003_250)] transition-colors disabled:opacity-40 disabled:cursor-default"
                >
                  {updateWorkspace.isPending ? 'Saving…' : 'Save'}
                </button>
              )}
            </div>
            {renameError && <p className="text-[12px] text-[var(--err)]">{renameError}</p>}
            {!isOwner && <p className="text-[11.5px] text-[var(--text-dim)] font-mono">Only owners can rename the workspace.</p>}
          </div>

          {/* Workspace ID */}
          <div className="flex flex-col gap-3 p-5 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px]">
            <div>
              <div className="text-[13.5px] font-semibold text-[var(--text)]">Workspace ID</div>
              <p className="text-[12px] text-[var(--text-faint)] mt-0.5">Use in API calls targeting this workspace.</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[12px] text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] px-3 py-1.5 rounded-[7px] select-all">
                {currentWorkspaceId ?? '—'}
              </span>
              <button
                onClick={() => { if (currentWorkspaceId) { navigator.clipboard.writeText(currentWorkspaceId); toast('Copied', { variant: 'ok' }) }}}
                className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-[7px] text-[12px] text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] hover:text-[var(--text)] transition-colors"
              >
                <Icons.Copy className="w-[12px] h-[12px]" /> Copy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Danger zone tab ── */}
      {tab === 'danger' && (
        <div className="flex flex-col gap-4">
          {/* Leave workspace — non-owners only */}
          {!isOwner && (
            <div className="flex items-center justify-between gap-6 p-5 bg-[var(--bg)] border border-[oklch(0.70_0.18_22/0.25)] rounded-[12px]">
              <div>
                <div className="text-[13.5px] font-semibold text-[var(--text)]">Leave workspace</div>
                <p className="text-[12px] text-[var(--text-faint)] mt-0.5 max-w-sm">
                  You'll lose access to all workflows and data in <strong className="text-[var(--text-mute)]">{currentWorkspace?.name}</strong>. You can be re-invited later.
                </p>
              </div>
              {!leaveConfirmOpen ? (
                <button
                  onClick={() => setLeaveConfirmOpen(true)}
                  className="shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-[9px] border border-[oklch(0.70_0.18_22/0.4)] text-[var(--err)] text-[13px] font-medium bg-transparent hover:bg-[oklch(0.70_0.18_22/0.08)] transition-colors"
                >
                  <Icons.Trash className="w-[13px] h-[13px]" />
                  Leave workspace
                </button>
              ) : (
                <div className="shrink-0 flex flex-col items-end gap-2">
                  <p className="text-[12px] text-[var(--err)] font-medium text-right">Are you sure?</p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setLeaveConfirmOpen(false)}
                      className="px-3 py-1.5 rounded-[7px] text-[12.5px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleLeave}
                      disabled={leavePending}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[7px] text-[12.5px] font-medium text-[var(--bg)] bg-[var(--err)] hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-default"
                    >
                      {leavePending ? 'Leaving…' : 'Yes, leave'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Delete workspace — owners only, non-personal */}
          {isOwner && !currentWorkspace?.is_personal && (
            <div className="flex flex-col gap-4 p-5 bg-[var(--bg)] border border-[oklch(0.70_0.18_22/0.25)] rounded-[12px]">
              <div className="flex items-start justify-between gap-6">
                <div>
                  <div className="text-[13.5px] font-semibold text-[var(--text)]">Delete workspace</div>
                  <p className="text-[12px] text-[var(--text-faint)] mt-0.5 max-w-sm">
                    Permanently deletes <strong className="text-[var(--text-mute)]">{currentWorkspace?.name}</strong> and all its workflows, members, and data. Cannot be undone.
                  </p>
                </div>
                {!deleteOpen && (
                  <button
                    onClick={() => setDeleteOpen(true)}
                    className="shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-[9px] border border-[oklch(0.70_0.18_22/0.4)] text-[var(--err)] text-[13px] font-medium bg-transparent hover:bg-[oklch(0.70_0.18_22/0.08)] transition-colors"
                  >
                    <Icons.Trash className="w-[13px] h-[13px]" />
                    Delete workspace
                  </button>
                )}
              </div>

              {deleteOpen && (
                <div className="flex flex-col gap-3 pt-4 border-t border-[oklch(0.70_0.18_22/0.2)]">
                  <p className="text-[12.5px] text-[var(--err)]">
                    Type <strong>{currentWorkspace?.name}</strong> to confirm deletion:
                  </p>
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      value={deleteConfirmName}
                      onChange={e => setDeleteConfirmName(e.target.value)}
                      placeholder={currentWorkspace?.name}
                      className="flex-1 max-w-sm px-3 h-[38px] bg-[var(--bg-2)] border border-[oklch(0.70_0.18_22/0.4)] rounded-[9px] text-[13px] text-[var(--text)] placeholder:text-[var(--text-dim)] outline-none focus:border-[var(--err)] transition-colors"
                    />
                    <button
                      onClick={handleDelete}
                      disabled={deleteConfirmName !== currentWorkspace?.name || deleteWorkspace.isPending}
                      className="inline-flex items-center gap-2 px-4 h-[38px] rounded-[9px] bg-[var(--err)] text-white text-[13px] font-medium border-none cursor-pointer hover:opacity-90 transition-opacity disabled:opacity-30 disabled:cursor-default shrink-0"
                    >
                      {deleteWorkspace.isPending ? 'Deleting…' : 'Delete permanently'}
                    </button>
                    <button
                      onClick={() => { setDeleteOpen(false); setDeleteConfirmName('') }}
                      className="px-3 h-[38px] rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Personal workspace — cannot delete */}
          {isOwner && currentWorkspace?.is_personal && (
            <div className="flex items-start gap-3 px-4 py-3.5 bg-[var(--surface)] border border-[var(--border-faint)] rounded-[10px]">
              <Icons.Activity className="w-[14px] h-[14px] text-[var(--text-faint)] shrink-0 mt-0.5" />
              <p className="text-[12px] text-[var(--text-faint)] m-0">
                Personal workspaces cannot be deleted.
              </p>
            </div>
          )}

          {/* Owner can't leave note */}
          {isOwner && !currentWorkspace?.is_personal && (
            <div className="flex items-start gap-3 px-4 py-3.5 bg-[var(--surface)] border border-[var(--border-faint)] rounded-[10px]">
              <Icons.Activity className="w-[14px] h-[14px] text-[var(--text-faint)] shrink-0 mt-0.5" />
              <p className="text-[12px] text-[var(--text-faint)] m-0">
                Owners cannot leave a workspace. Transfer ownership to a member first, or delete the workspace above.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

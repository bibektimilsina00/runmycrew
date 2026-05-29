import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { Button } from '@/shared/components/Button'
import { useCreateInvite } from '../hooks/useWorkspace'
import { useWorkspaceStore } from '../store/workspaceStore'
import type { WorkspaceRole, WorkspaceInvite } from '../types/workspaceTypes'
import { RoleSelect } from './RoleSelect'

const ROLES: WorkspaceRole[] = ['admin', 'member', 'viewer']

export function InviteForm() {
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const createInvite = useCreateInvite(workspaceId)

  const [email, setEmail] = useState('')
  const [role, setRole] = useState<WorkspaceRole>('member')
  const [sendEmail, setSendEmail] = useState(false)
  const [latestInvite, setLatestInvite] = useState<WorkspaceInvite | null>(null)
  const [copied, setCopied] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return
    const invite = await createInvite.mutateAsync({ email, role, send_email: sendEmail })
    setLatestInvite(invite)
    setEmail('')
  }

  const handleCopy = async () => {
    if (!latestInvite) return
    await navigator.clipboard.writeText(latestInvite.invite_url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col gap-[10px]">
      <form className="grid grid-cols-[1fr_120px_auto] gap-[8px]" onSubmit={handleSubmit}>
        <input
          className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[var(--text)] text-[13px] px-[12px] py-[8px] outline-none transition-colors duration-120 focus:border-[var(--border)] placeholder:text-[var(--text-faint)] h-[37px]"
          type="email"
          placeholder="teammate@company.com"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
        />
        <RoleSelect
          value={role}
          options={ROLES}
          onChange={setRole}
          className="h-[37px] px-[12px] bg-[var(--bg)] text-[13px]"
        />
        <Button
          type="submit"
          variant="primary"
          leftIcon={<Icons.Plus />}
          loading={createInvite.isPending}
          className="h-[37px] px-[20px] rounded-[9px]"
        >
          {createInvite.isPending ? 'Sending…' : 'Invite'}
        </Button>
      </form>

      <label className="inline-flex items-center gap-[8px] text-[12px] text-[var(--text-faint)] cursor-pointer mt-1">
        <input
          className="cursor-pointer accent-[var(--text)]"
          type="checkbox"
          checked={sendEmail}
          onChange={e => setSendEmail(e.target.checked)}
        />
        Send email notification
      </label>

      {latestInvite && (
        <div className="flex items-center gap-[10px] px-[14px] py-[10px] bg-[var(--surface)] border border-[var(--border-faint)] rounded-[9px] mt-2">
          <Icons.Link style={{ width: 13, height: 13, color: 'var(--text-faint)', flexShrink: 0 }} />
          <span className="flex-1 min-w-0 text-[11.5px] font-mono text-[var(--text-mute)] overflow-hidden text-ellipsis whitespace-nowrap">{latestInvite.invite_url}</span>
          <button className="inline-flex items-center gap-[5px] px-[10px] py-[5px] rounded-[7px] bg-[var(--surface-2)] border border-[var(--border-faint)] text-[var(--text-mute)] text-[11.5px] font-medium cursor-pointer transition-colors duration-80 whitespace-nowrap hover:bg-[var(--surface-3)] hover:text-[var(--text)]" onClick={handleCopy} type="button">
            {copied ? <Icons.Check style={{ width: 12, height: 12, color: 'var(--ok)' }} /> : <Icons.Copy style={{ width: 12, height: 12 }} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      )}

      {createInvite.isError && (
        <p className="text-[12px] text-[var(--err)] m-0">{createInvite.error?.message ?? 'Failed to create invite'}</p>
      )}
    </div>
  )
}

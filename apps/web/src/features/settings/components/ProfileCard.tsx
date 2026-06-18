import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import type { UserProfile } from '../types/settingsTypes'

interface Props {
  profile: UserProfile
  onSave: (fullName: string, password?: string) => Promise<void>
  isSaving?: boolean
}

export function ProfileCard({ profile, onSave, isSaving = false }: Props) {
  const [fullName, setFullName] = useState(profile.full_name || '')
  const [prevFullName, setPrevFullName] = useState(profile.full_name || '')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (profile.full_name !== prevFullName) {
    setFullName(profile.full_name || '')
    setPrevFullName(profile.full_name || '')
  }

  const initial = (profile.full_name || profile.email || '?')[0].toUpperCase()
  const joinedDate = profile.created_at
    ? new Date(profile.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : '—'

  const handleSave = async () => {
    setError(null)
    if (!fullName.trim()) { setError('Full name cannot be empty.'); return }
    if (password) {
      if (password.length < 8) { setError('Password must be at least 8 characters.'); return }
      if (password !== confirmPassword) { setError('Passwords do not match.'); return }
    }
    try {
      await onSave(fullName.trim(), password || undefined)
      setPassword('')
      setConfirmPassword('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes.')
    }
  }

  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[var(--border-faint)]">
        <div className="flex items-center gap-2 text-[14px] font-semibold text-[var(--text)] tracking-tight">
          <Icons.Users className="w-[14px] h-[14px] text-[var(--text-faint)]" />
          Profile information
        </div>
        <p className="text-[12px] text-[var(--text-faint)] mt-1">Update your name and password.</p>
      </div>

      <div className="p-6 flex flex-col gap-6">
        {/* Avatar row */}
        <div className="flex items-center gap-4">
          <div className="w-[52px] h-[52px] rounded-[12px] bg-[var(--text)] text-[var(--bg)] flex items-center justify-center text-[20px] font-bold tracking-tight shrink-0">
            {initial}
          </div>
          <div className="flex flex-col gap-1 min-w-0">
            <span className="text-[14px] font-semibold text-[var(--text)] tracking-tight truncate">
              {profile.full_name || 'No name set'}
            </span>
            <span className="text-[12px] font-mono text-[var(--text-faint)] truncate">{profile.email}</span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold tracking-widest uppercase px-[7px] py-[3px] rounded-[4px] bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]">
                <Icons.Check className="w-[9px] h-[9px]" /> Active
              </span>
              <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[var(--text-dim)]">
                <Icons.Clock className="w-[10px] h-[10px]" /> Joined {joinedDate}
              </span>
            </div>
          </div>
        </div>

        <div className="h-px bg-[var(--border-faint)]" />

        {/* Fields grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Full name */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[11.5px] font-medium text-[var(--text-mute)]">Full name</label>
            <div className="flex items-center gap-2.5 px-3 h-[38px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] focus-within:border-[var(--border)] transition-colors">
              <Icons.Users className="w-[14px] h-[14px] text-[var(--text-faint)] shrink-0" />
              <input
                type="text"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                placeholder="Your name"
                className="flex-1 bg-transparent border-none outline-none text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)]"
              />
            </div>
          </div>

          {/* Email — read only */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[11.5px] font-medium text-[var(--text-mute)]">Email address</label>
            <div className="flex items-center gap-2.5 px-3 h-[38px] bg-[var(--surface)] border border-[var(--border-faint)] rounded-[9px] opacity-60 cursor-not-allowed">
              <Icons.Feedback className="w-[14px] h-[14px] text-[var(--text-faint)] shrink-0" />
              <input
                type="email"
                value={profile.email}
                disabled
                className="flex-1 bg-transparent border-none outline-none text-[13px] text-[var(--text-mute)] cursor-not-allowed"
              />
            </div>
          </div>

          {/* New password */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[11.5px] font-medium text-[var(--text-mute)]">
              New password <span className="text-[var(--text-dim)] font-normal">(optional)</span>
            </label>
            <div className="flex items-center gap-2.5 px-3 h-[38px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] focus-within:border-[var(--border)] transition-colors">
              <Icons.Key className="w-[14px] h-[14px] text-[var(--text-faint)] shrink-0" />
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Min. 8 characters"
                className="flex-1 bg-transparent border-none outline-none text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)]"
              />
            </div>
          </div>

          {/* Confirm password */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[11.5px] font-medium text-[var(--text-mute)]">Confirm password</label>
            <div className="flex items-center gap-2.5 px-3 h-[38px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] focus-within:border-[var(--border)] transition-colors">
              <Icons.Key className="w-[14px] h-[14px] text-[var(--text-faint)] shrink-0" />
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                className="flex-1 bg-transparent border-none outline-none text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)]"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="text-[12px] text-[var(--err)] bg-[oklch(0.70_0.18_22/0.10)] border border-[oklch(0.70_0.18_22/0.25)] px-3 py-2.5 rounded-[8px]">
            {error}
          </div>
        )}

        <div className="flex justify-end">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--accent)] text-white text-[13px] font-medium border-none cursor-pointer transition-colors hover:brightness-110 disabled:opacity-50 disabled:cursor-default"
          >
            <Icons.Check className="w-[13px] h-[13px]" />
            {isSaving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </div>
    </div>
  )
}

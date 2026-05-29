import { useState } from 'react'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useToast } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import { useSettings, useUpdateProfile } from '../hooks/useSettings'
import { ProfileCard } from '../components/ProfileCard'
import { ApiKeysCard } from '../components/ApiKeysCard'
import type { UserProfile } from '../types/settingsTypes'

export function Settings() {
  const { user } = useAuth()
  const { toast } = useToast()
  const { apiKeys, isGenerating, createApiKey, revokeApiKey } = useSettings()
  const updateProfileMutation = useUpdateProfile()

  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const profile: UserProfile = {
    id: user?.id || '',
    email: user?.email || '',
    full_name: user?.full_name || '',
    avatar_url: user?.avatar_url || undefined,
    is_active: user?.is_active ?? true,
    created_at: user?.created_at || new Date().toISOString(),
  }

  const handleSaveProfile = async (fullName: string, password?: string) => {
    await updateProfileMutation.mutateAsync({ fullName, password })
    toast('Profile updated', { variant: 'ok', description: 'Your details were successfully saved.' })
  }

  const handleCreateKey = async (name: string) => {
    try {
      const newKey = await createApiKey(name)
      if (newKey.token) { setNewlyCreatedKey(newKey.token); setCopied(false) }
      toast('API key generated', { variant: 'ok', description: 'New developer key created.' })
      return newKey
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Please try again.'
      toast('Failed to generate key', { variant: 'err', description: msg })
      throw err
    }
  }

  const handleRevokeKey = async (id: string, name: string) => {
    try {
      await revokeApiKey(id)
      toast('API key revoked', { variant: 'ok', description: `Revoked: ${name}` })
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Please try again.'
      toast('Failed to revoke key', { variant: 'err', description: msg })
    }
  }

  const handleCopy = () => {
    if (!newlyCreatedKey) return
    navigator.clipboard.writeText(newlyCreatedKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Account</span>
          <h1>Settings</h1>
        </div>
      </div>

      <ProfileCard
        profile={profile}
        onSave={handleSaveProfile}
        isSaving={updateProfileMutation.isPending}
      />

      <ApiKeysCard
        apiKeys={apiKeys}
        isGenerating={isGenerating}
        onCreateKey={handleCreateKey}
        onRevokeKey={handleRevokeKey}
      />

      {/* New key reveal modal */}
      {newlyCreatedKey && (
        <>
          <div
            className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm"
            onClick={() => setNewlyCreatedKey(null)}
          />
          <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[480px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[16px] p-6 flex flex-col gap-5 shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]">
            {/* Title */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-[15px] font-semibold text-[var(--text)] tracking-tight">API key generated</h3>
                <p className="text-[12.5px] text-[var(--text-faint)] mt-1">
                  Copy this key now — it won't be shown again.
                </p>
              </div>
              <button
                onClick={() => setNewlyCreatedKey(null)}
                className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Warning */}
            <div className="flex items-start gap-3 bg-[oklch(0.82_0.14_80/0.12)] border border-[oklch(0.82_0.14_80/0.3)] px-3.5 py-3 rounded-[9px]">
              <Icons.Activity className="w-[14px] h-[14px] text-[var(--warn)] shrink-0 mt-0.5" />
              <p className="text-[12px] text-[var(--warn)] m-0">
                Store this key securely. Once closed, you cannot retrieve it.
              </p>
            </div>

            {/* Key + copy */}
            <div className="flex gap-2">
              <div className="flex-1 flex items-center px-3 h-[38px] bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] font-mono text-[12px] text-[var(--text-mute)] overflow-hidden">
                <span className="truncate select-all">{newlyCreatedKey}</span>
              </div>
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-2 px-3.5 h-[38px] rounded-[9px] bg-[var(--surface)] border border-[var(--border-faint)] text-[13px] font-medium text-[var(--text-mute)] hover:bg-[var(--surface-2)] hover:text-[var(--text)] transition-colors shrink-0"
              >
                {copied
                  ? <><Icons.Check className="w-[13px] h-[13px] text-[var(--ok)]" /> Copied</>
                  : <><Icons.Copy className="w-[13px] h-[13px]" /> Copy</>
                }
              </button>
            </div>

            <div className="flex justify-end pt-1 border-t border-[var(--border-faint)]">
              <button
                onClick={() => setNewlyCreatedKey(null)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors"
              >
                I've saved this key
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

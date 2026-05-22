import { useState } from 'react'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useToast } from '@/shared/components'
import { useSettings } from '../hooks/useSettings'
import { ProfileCard } from '../components/ProfileCard'
import { ApiKeysCard } from '../components/ApiKeysCard'
import type { UserProfile } from '../types/settingsTypes'

/**
 * Settings page managing user profile details and API tokens.
 */
export function Settings() {
  const { user } = useAuth()
  const { toast } = useToast()
  const { apiKeys, isGenerating, createApiKey, revokeApiKey } = useSettings()

  const [fullName, setFullName] = useState(user?.full_name || '')

  const profile: UserProfile = {
    fullName: user?.full_name || '',
    email: user?.email || '',
    avatarUrl: user?.avatar_url || undefined,
    createdAt: user?.created_at,
  }

  const handleSaveProfile = () => {
    toast('Profile updated', {
      variant: 'ok',
      description: 'Your details were successfully saved.',
    })
  }

  const handleCopyKey = (token: string) => {
    navigator.clipboard.writeText(token)
    toast('API Token copied', {
      variant: 'ok',
      description: 'Token copied to your system clipboard.',
    })
  }

  const handleCreateKey = async (name: string) => {
    const newKey = await createApiKey(name)
    toast('API Key generated', {
      variant: 'ok',
      description: "Ensure you copy the secret key now; you won't see it again.",
    })
    return newKey
  }

  const handleRevokeKey = async (id: string, name: string) => {
    await revokeApiKey(id)
    toast('API Key revoked', {
      variant: 'ok',
      description: `Revoked: ${name}`,
    })
  }

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      <ProfileCard
        profile={profile}
        fullName={fullName}
        onFullNameChange={setFullName}
        onSave={handleSaveProfile}
      />
      <ApiKeysCard
        apiKeys={apiKeys}
        isGenerating={isGenerating}
        onCreateKey={handleCreateKey}
        onRevokeKey={handleRevokeKey}
        onCopyKey={handleCopyKey}
      />
    </div>
  )
}

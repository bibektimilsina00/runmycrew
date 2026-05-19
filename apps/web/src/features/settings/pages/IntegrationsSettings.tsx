import React, { useState, useEffect } from 'react'
import { Plus, Trash2, Key, RefreshCw } from 'lucide-react'
import { SettingsPageContainer, SettingsPageHeader } from '@/features/settings/components/shared/SettingsLayout'
import { SettingsSearchInput, SettingsButton } from '@/features/settings/components/shared/SettingsInputs'
import { SettingsItem, SettingsSection } from '@/features/settings/components/shared/SettingsList'
import AddCredentialModal from '@/features/credentials/AddCredentialModal'
import { useCredentialsManagement } from '@/features/credentials/hooks/use-credentials-management'
import { Spinner, IconButton } from '@/components/ui'
import api from '@/lib/api/client'
import { logger } from '@/lib/logger'

export const IntegrationsSettings: React.FC = () => {
  const {
    credentials,
    isLoading: isCredentialsLoading,
    isDeleting,
    searchQuery,
    setSearchQuery,
    isModalOpen,
    selectedService,
    setSelectedService,
    openModal,
    closeModal,
    handleDelete,
    refresh
  } = useCredentialsManagement()

  const [supportedProviders, setSupportedProviders] = useState<any[]>([])
  const [isProvidersLoading, setIsProvidersLoading] = useState(false)

  // Fetch providers directly for the list
  useEffect(() => {
    const fetchProviders = async () => {
      setIsProvidersLoading(true)
      try {
        const response = await api.get('/credentials/providers')
        // Only show integrations (not byok types) in this list
        setSupportedProviders(response.data.filter((p: any) => p.id.includes('oauth') || p.id === 'github_pat'))
      } catch (err) {
        logger.error('Failed to fetch providers:', err)
      } finally {
        setIsProvidersLoading(false)
      }
    }

    fetchProviders()
  }, [])

  const handleConnectProvider = (provider: any) => {
    setSelectedService(provider)
    openModal()
  }

  const handleOpenMainConnect = () => {
    setSelectedService(null)
    openModal()
  }

  const getServiceIcon = (type: string) => {
    const service = supportedProviders.find(p => p.id === type || p.id.startsWith(type.split('_')[0]))
    if (service?.icon_url) {
      return <img src={service.icon_url} alt={service.name} className="w-5 h-5 object-contain" />
    }
    return <Key size={18} />
  }

  return (
    <SettingsPageContainer>
      <SettingsPageHeader title="Integrations" />

      <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
        {/* Toolbar */}
        <div className="flex items-center gap-2 mb-8">
          <SettingsSearchInput 
            placeholder="Search your integrations..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <div className="flex shrink-0 items-center gap-2">
            <IconButton
              icon={<RefreshCw size={16} className={isCredentialsLoading ? 'animate-spin' : ''} />}
              tooltip="Refresh list"
              onClick={() => refresh()}
            />
            <SettingsButton variant="primary" onClick={handleOpenMainConnect} className="gap-1.5">
              <Plus />
              Connect
            </SettingsButton>
          </div>
        </div>

        <SettingsSection label="Available integrations">
          <div className="flex flex-col gap-1">
            {isProvidersLoading ? (
              <div className="py-4 flex justify-center">
                <Spinner size="sm" color="muted" />
              </div>
            ) : (
              supportedProviders.map((provider) => (
                <SettingsItem
                  key={provider.id}
                  title={provider.name}
                  subtitle={provider.description}
                  icon={
                    <div className="w-8 h-8 bg-surface-5 rounded-lg flex items-center justify-center overflow-hidden">
                      {provider.icon_url ? (
                        <img src={provider.icon_url} alt={provider.name} className="w-5 h-5 object-contain" />
                      ) : (
                        <Key size={18} className="text-text-muted" />
                      )}
                    </div>
                  }
                  action={
                    <SettingsButton size="sm" variant="primary" onClick={() => handleConnectProvider(provider)}>
                      Connect
                    </SettingsButton>
                  }
                />
              ))
            )}
          </div>
        </SettingsSection>

        <SettingsSection label="Your Connected Accounts" className="mt-8">
          {isCredentialsLoading ? (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <Spinner size="sm" color="accent" className="mb-3" />
              <p className="text-xs">Loading integrations...</p>
            </div>
          ) : credentials.length === 0 ? (
            <div className="py-12 flex flex-col items-center text-center">
              <div className="w-12 h-12 bg-surface-5/50 rounded-xl flex items-center justify-center text-text-muted mb-4">
                <Key size={24} />
              </div>
              <p className="text-sm text-text-muted">
                {searchQuery ? "No integrations match your search." : "No connected accounts yet."}
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-1">
              {credentials.map((cred) => (
                <SettingsItem
                  key={cred.id}
                  title={cred.name}
                  subtitle={`${cred.type.replace(/_/g, ' ').toUpperCase()} · Added ${new Date(cred.created_at).toLocaleDateString()}`}
                  icon={
                    <div className="w-8 h-8 bg-surface-5 rounded-lg flex items-center justify-center overflow-hidden group-hover:scale-110 transition-transform">
                      {getServiceIcon(cred.type)}
                    </div>
                  }
                  action={
                    <IconButton
                      icon={<Trash2 size={16} />}
                      tooltip="Delete integration"
                      variant="danger"
                      onClick={() => handleDelete(cred.id)}
                      disabled={isDeleting}
                      className="opacity-0 group-hover:opacity-100"
                    />
                  }
                />
              ))}
            </div>
          )}
        </SettingsSection>
      </div>

      {/* Unified Integration Modal (Selection or Configuration) */}
      <AddCredentialModal 
        isOpen={isModalOpen} 
        onClose={closeModal} 
        initialService={selectedService}
        allowedProviders={supportedProviders}
      />
    </SettingsPageContainer>
  )
}

import { useMemo, useState } from 'react'
import {
  Dropdown, DropdownTrigger, DropdownContent, DropdownItem, DropdownSeparator,
} from './Dropdown'
import { Icons } from './icons'
import { useCredentials, useProviders } from '@/features/connections/hooks/useConnections'
import { ConnectModal } from '@/features/connections/components/ConnectModal'

interface Props {
  /** Credential type to filter by (e.g. 'openai_api_key', 'google_api_key'). */
  credType: string
  /** Currently selected credential id (empty string = none selected). */
  value: string
  onChange: (credentialId: string) => void
  /** Friendly provider label shown in placeholder. */
  providerLabel?: string
  /** Disable the selector. */
  disabled?: boolean
  className?: string
}

/**
 * Global credential picker.
 *
 * - Lists all credentials of the given `credType`.
 * - Always shows a trailing "+ Create new credential" item that opens
 *   `ConnectModal` preselected to the matching provider. On creation, the new
 *   credential is auto-selected.
 *
 * Designed for any feature that needs the user to pick (or create) a
 * credential of a specific type — KB embeddings, AI nodes, integrations, etc.
 */
export function CredentialSelector({
  credType,
  value,
  onChange,
  providerLabel,
  disabled,
  className,
}: Props) {
  const { data: credentials = [] } = useCredentials()
  const { data: providers   = [] } = useProviders()

  const [showConnect, setShowConnect] = useState(false)

  const relevant = useMemo(
    () => credentials.filter(c => c.type === credType),
    [credentials, credType]
  )
  const selected = relevant.find(c => c.id === value)

  // Provider name for ConnectModal preselection. If providers haven't loaded
  // yet, fall back to credType so the modal at least shows the catalog.
  const providerId = providers.find(p => p.id === credType)?.id ?? credType
  const label = providerLabel
    ?? providers.find(p => p.id === credType)?.name
    ?? credType.replace(/_/g, ' ')

  return (
    <>
      <Dropdown className={className ?? 'w-full'}>
        <DropdownTrigger className="w-full" disabled={disabled}>
          <div className="flex items-center justify-between h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] cursor-pointer hover:border-[var(--border-soft)] transition-colors">
            <span className={selected ? 'text-[var(--text)]' : 'text-[var(--text-faint)]'}>
              {selected?.name ?? `Select ${label} credential…`}
            </span>
            <Icons.Caret style={{ width: 11, height: 11, color: 'var(--text-faint)' }} />
          </div>
        </DropdownTrigger>
        <DropdownContent className="w-full">
          {relevant.length === 0 && (
            <div className="px-3 py-2 text-[12px] text-[var(--text-faint)]">
              No {label} credentials yet.
            </div>
          )}
          {relevant.map(c => (
            <DropdownItem
              key={c.id}
              onClick={() => onChange(c.id)}
              className={value === c.id ? 'bg-[var(--surface)]' : ''}
            >
              <div className="flex items-center justify-between w-full">
                <span className="truncate">{c.name}</span>
                {value === c.id && (
                  <Icons.Check style={{ width: 13, height: 13, color: 'var(--ok)' }} />
                )}
              </div>
            </DropdownItem>
          ))}
          {relevant.length > 0 && <DropdownSeparator />}
          <DropdownItem
            onClick={() => setShowConnect(true)}
            leftIcon={<Icons.Plus />}
          >
            <span className="text-[var(--accent)]">Create new {label} credential</span>
          </DropdownItem>
        </DropdownContent>
      </Dropdown>

      {showConnect && (
        <ConnectModal
          providers={providers}
          initialProviderId={providerId}
          onClose={() => setShowConnect(false)}
          onCreated={(newId) => { if (newId) onChange(newId) }}
        />
      )}
    </>
  )
}

import { useMemo, useState, type CSSProperties } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/cn'
import {
  Dropdown, DropdownTrigger, DropdownContent, DropdownItem, DropdownSeparator,
} from '@/components/ui/dropdown-menu'
import { Icons } from './icons'
import { useCredentials, useProviders } from '@/features/connections/hooks/useConnections'
import { ConnectModal } from '@/features/connections/components/ConnectModal'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'
import type { Provider } from '@/features/connections/types/connectionsTypes'

/** Small brand-icon tile used in both the dropdown trigger and each
 *  credential row. Reads `icon_slug` + `color` straight off the
 *  provider — backend owns the visuals. Falls back to a single-letter
 *  monogram for providers without a slug.
 *
 *  Wrapped in a `marginRight: 10` style so the gap between tile and
 *  label is enforced regardless of how the host (DropdownItem slot,
 *  trigger row) lays out its children. Using the slot's flex `gap`
 *  was unreliable — Tailwind class merging let the parent's `gap-2`
 *  win over our `!gap-3` override in some renders. */
function ProviderTile({ provider, size }: { provider: Provider | undefined; size: number }) {
  const dim = `${size}px`
  const wrapperStyle: CSSProperties = {}
  if (!provider?.icon_slug) {
    return (
      <span
        className="inline-flex shrink-0 items-center justify-center rounded-[5px] bg-[var(--surface-2)] text-[10px] font-semibold text-[var(--text)]"
        style={{ width: dim, height: dim, ...wrapperStyle }}
      >
        {(provider?.name ?? '?').charAt(0).toUpperCase()}
      </span>
    )
  }
  const inner = size - Math.max(1, Math.round(size / 6)) * 2
  return (
    <span
      className="inline-flex shrink-0 items-center justify-center rounded-[5px]"
      style={{
        width: dim,
        height: dim,
        background: provider.color ?? 'var(--surface)',
        padding: Math.max(1, Math.round(size / 6)),
        ...wrapperStyle,
      }}
    >
      <BrandIcon
        slug={provider.icon_slug}
        className="object-contain"
        style={{ width: inner, height: inner }}
      />
    </span>
  )
}

interface Props {
  /** Credential type(s) to filter by. Pass an array when a feature accepts
   *  multiple types (e.g. IG nodes accept both `meta_oauth` and
   *  `instagram_oauth`). The "+ Create new" modal opens preselected to
   *  the first entry; user can switch inside the modal. */
  credType: string | string[]
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

  const credTypes = useMemo<string[]>(
    () => (Array.isArray(credType) ? credType : [credType]),
    [credType]
  )
  const primaryType = credTypes[0] ?? ''
  const relevant = useMemo(
    () => credentials.filter(c => credTypes.includes(c.type)),
    [credentials, credTypes]
  )
  const selected = relevant.find(c => c.id === value)

  // Provider name for ConnectModal preselection. If providers haven't loaded
  // yet, fall back to the primary credType so the modal at least shows the catalog.
  const providerId = providers.find(p => p.id === primaryType)?.id ?? primaryType
  const label = providerLabel
    ?? providers.find(p => p.id === primaryType)?.name
    ?? primaryType.replace(/_/g, ' ')

  const selectedProvider = selected ? providers.find(p => p.id === selected.type) : undefined

  return (
    <>
      <Dropdown>
        <DropdownTrigger asChild disabled={disabled}>
          <div className={cn(
            "flex items-center !gap-3 w-full h-9 pl-2 pr-2.5 text-sm text-left bg-surface border border-border-soft rounded-[8px] cursor-pointer",
            "transition-[background-color,border-color] duration-[120ms]",
            "hover:border-border hover:bg-surface-2 focus:outline-none focus:border-accent focus:bg-surface-2",
            "data-[state=open]:border-accent data-[state=open]:bg-surface-2",
            className
          )}>
            {selected && <ProviderTile provider={selectedProvider} size={20} />}
            <span className={cn('truncate', selected ? 'text-text' : 'text-text-faint')}>
              {selected?.name ?? `Select ${label} credential…`}
            </span>
            <ChevronDown className="ml-auto shrink-0 w-3.5 h-3.5 text-text-faint" />
          </div>
        </DropdownTrigger>
        <DropdownContent className="w-[var(--radix-dropdown-menu-trigger-width)] min-w-[var(--radix-dropdown-menu-trigger-width)]">
          {relevant.length === 0 && (
            <div className="px-3 py-2 text-[12px] text-[var(--text-faint)]">
              No {label} credentials yet.
            </div>
          )}
          {relevant.map(c => {
            const rowProvider = providers.find(p => p.id === c.type)
            return (
              <DropdownItem
                key={c.id}
                onClick={() => onChange(c.id)}
                leftIcon={<ProviderTile provider={rowProvider} size={18} />}
                rightIcon={
                  value === c.id
                    ? <Icons.Check style={{ width: 13, height: 13, color: 'var(--accent)' }} />
                    : undefined
                }
                className={cn(
                  value === c.id ? 'bg-surface-2 font-medium text-text' : 'text-text-mute'
                )}
              >
                <span className="truncate">{c.name}</span>
              </DropdownItem>
            )
          })}
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

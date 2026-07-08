import { useMemo, useState, type CSSProperties } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/cn'
import {
  Dropdown, DropdownTrigger, DropdownContent, DropdownSeparator,
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
            "transition-[background-color,border-color] [transition-duration:120ms]",
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
        <DropdownContent className="w-[var(--radix-dropdown-menu-trigger-width)] min-w-[var(--radix-dropdown-menu-trigger-width)] overflow-hidden rounded-[10px] p-0">
          {/* Empty state — treated as a card, not a list row. Big brand
              tile at top, one clear CTA at the bottom. When the user
              has creds this whole block is replaced by the list + a
              compact new-connection row. */}
          {relevant.length === 0 ? (
            <div className="px-5 pb-4 pt-6">
              <div className="flex flex-col items-center gap-3 pb-4 text-center">
                <div
                  className="relative flex h-14 w-14 items-center justify-center rounded-[12px] [&_img]:h-9 [&_img]:w-9 [&_img]:object-contain"
                  style={{
                    background: providers.find(p => p.id === primaryType)?.color ?? 'var(--surface-2)',
                  }}
                >
                  <ProviderTile provider={providers.find(p => p.id === primaryType)} size={54} />
                </div>
                <div>
                  <p className="text-[14px] font-semibold text-[var(--text)]">
                    Connect {label}
                  </p>
                  <p className="mt-0.5 text-[12px] text-[var(--text-mute)]">
                    Link your {label} account to use this node.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowConnect(true)}
                className={cn(
                  'flex w-full items-center justify-center gap-2 rounded-[9px] px-3 py-2.5',
                  'bg-[var(--accent)] text-[13px] font-medium text-white',
                  'transition-[filter,transform] duration-100',
                  'hover:brightness-110 active:scale-[0.99]',
                  'shadow-[0_1px_0_oklch(1_0_0/0.08)_inset,0_6px_16px_-6px_oklch(0.55_0.19_275/0.6)]',
                )}
              >
                <Icons.Plug style={{ width: 13, height: 13 }} />
                Connect {label}
              </button>
            </div>
          ) : (
            <div className="p-1.5">
              <div className="px-2 pb-1.5 pt-1 text-[9.5px] font-semibold uppercase tracking-widest text-[var(--text-dim)]">
                {label} · {relevant.length}
              </div>
              {relevant.map(c => {
                const rowProvider = providers.find(p => p.id === c.type)
                const active = value === c.id
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => onChange(c.id)}
                    className={cn(
                      'group flex w-full items-center gap-2.5 rounded-[7px] px-2 py-1.5 text-left transition-colors',
                      active
                        ? 'bg-[color-mix(in_oklab,var(--accent)_16%,transparent)]'
                        : 'hover:bg-[var(--surface)]',
                    )}
                  >
                    <ProviderTile provider={rowProvider} size={22} />
                    <span className="flex min-w-0 flex-1 flex-col">
                      <span className={cn(
                        'truncate text-[12.5px]',
                        active ? 'font-semibold text-[var(--text)]' : 'font-medium text-[var(--text)]',
                      )}>
                        {c.name}
                      </span>
                      <span className="truncate text-[10.5px] text-[var(--text-faint)]">
                        {rowProvider?.type === 'oauth' ? 'OAuth' : 'API Key'}
                      </span>
                    </span>
                    {active && (
                      <Icons.Check style={{ width: 14, height: 14, color: 'var(--accent)' }} />
                    )}
                  </button>
                )
              })}
              <DropdownSeparator className="!my-1.5" />
              <button
                type="button"
                onClick={() => setShowConnect(true)}
                className={cn(
                  'flex w-full items-center gap-2.5 rounded-[7px] px-2 py-1.5 text-left transition-colors',
                  'hover:bg-[color-mix(in_oklab,var(--accent)_10%,transparent)]',
                )}
              >
                <span className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-[5px] bg-[color-mix(in_oklab,var(--accent)_18%,transparent)] text-[var(--accent)]">
                  <Icons.Plus style={{ width: 12, height: 12 }} />
                </span>
                <span className="truncate text-[12.5px] font-medium text-[var(--accent)]">
                  Connect another {label}
                </span>
              </button>
            </div>
          )}
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

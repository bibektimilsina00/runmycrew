import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, ExternalLink, Plug } from 'lucide-react'
import { Button } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useProviders } from '@/features/connections/hooks/useConnections'
import type { Credential, Provider } from '@/features/connections/types/connectionsTypes'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'

/**
 * One row inside the "Integrations required" section on the detail
 * page. Replaces the bare mono chips — shows provider icon, display
 * name, current connection status, and an inline Connect / Connected
 * affordance.
 *
 * `required` is the raw string from `template.credentials_required`
 * (could be `linear`, `action.linear`, `linear_oauth`, depending on
 * the source template). We normalise it inside and match against the
 * shared `/credentials/providers` catalog.
 */

interface IntegrationRowProps {
  required: string
  connected: Credential[]
}

export function IntegrationRow({ required, connected }: IntegrationRowProps) {
  const navigate = useNavigate()
  const { data: providers = [] } = useProviders()

  const normalised = normalise(required)

  const provider = useMemo<Provider | null>(() => {
    if (!normalised) return null
    return providers.find((p) => p.id.toLowerCase() === normalised) ?? null
  }, [providers, normalised])

  const isConnected = useMemo(() => {
    if (!normalised) return false
    return connected.some((c) => credentialMatches(c.type, normalised))
  }, [connected, normalised])

  const displayName = provider?.name ?? humanise(required)
  const description = provider?.description ?? `Required by this template.`

  return (
    <div className="flex items-center gap-3.5 rounded-[10px] border border-[var(--border-faint)] bg-[var(--surface)] p-4">
      <IntegrationIcon provider={provider} fallbackLetter={displayName.charAt(0)} />

      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <div className="flex items-center gap-2">
          <span className="truncate text-[14.5px] font-semibold text-[var(--text)] tracking-[-0.005em]">
            {displayName}
          </span>
          {isConnected ? (
            <span className="inline-flex items-center gap-1 rounded-[5px] bg-[var(--ok)]/12 px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-[0.06em] text-[var(--ok)]">
              <Check className="h-3 w-3" /> Connected
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-[5px] bg-[var(--warn)]/12 px-1.5 py-0.5 text-[10.5px] font-bold uppercase tracking-[0.06em] text-[var(--warn)]">
              Required
            </span>
          )}
        </div>
        <span className="truncate text-[12.5px] text-[var(--text-mute)]">{description}</span>
      </div>

      {isConnected ? (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
          leftIcon={<ExternalLink className="h-3.5 w-3.5" />}
          className="shrink-0"
        >
          Manage
        </Button>
      ) : (
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
          leftIcon={<Plug className="h-3.5 w-3.5" />}
          className="shrink-0 font-semibold"
        >
          Connect
        </Button>
      )}
    </div>
  )
}

function IntegrationIcon({
  provider,
  fallbackLetter,
}: {
  provider: Provider | null
  fallbackLetter: string
}) {
  if (provider?.icon_slug) {
    return (
      <div
        className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-[8px] border border-[var(--border-faint)] [&_img]:h-6 [&_img]:w-6 [&_img]:object-contain"
        style={{ background: provider.color ?? 'var(--bg)' }}
      >
        <BrandIcon slug={provider.icon_slug} />
      </div>
    )
  }
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-[8px] border border-[var(--border-faint)] bg-[var(--bg)]">
      <span className="text-[15px] font-semibold uppercase text-[var(--accent)]">
        {fallbackLetter.toUpperCase()}
      </span>
    </div>
  )
}

/**
 * Strip the common prefix/suffixes seeded templates may carry —
 * `action.linear` → `linear`, `slack_oauth` → `slack`, etc — so the
 * lookup against `Provider.id` matches consistently.
 */
function normalise(raw: string): string {
  const trimmed = raw.trim().toLowerCase()
  return trimmed
    .replace(/^action\./, '')
    .replace(/^trigger\./, '')
    .replace(/_oauth$/, '')
    .replace(/_api_key$/, '')
}

function humanise(raw: string): string {
  const n = normalise(raw)
  if (!n) return raw
  return n.charAt(0).toUpperCase() + n.slice(1)
}

function credentialMatches(credentialType: string, normalisedRequired: string): boolean {
  const t = credentialType.toLowerCase()
  return (
    t === normalisedRequired ||
    t === `${normalisedRequired}_oauth` ||
    t === `${normalisedRequired}_api_key` ||
    t.startsWith(`${normalisedRequired}_`)
  )
}

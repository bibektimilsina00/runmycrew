import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown, Loader2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import apiClient from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import type { RendererProps } from '../types'

/**
 * Field renderer for the `meta-resource` property type — used by Meta
 * trigger / action nodes to pick a specific Page, Instagram business
 * account, WhatsApp number, or Lead Ads form once the user picks a
 * `meta_oauth` credential upstream.
 *
 * The list is fetched lazily from `GET /meta/resources` and keyed on
 * `(credential_id, kind)`, so switching credentials immediately swaps
 * the dropdown contents without a manual refetch.
 */

interface MetaResource {
  id: string
  name: string
  kind: string
  secondary?: string | null
}

interface MetaResourcesResponse {
  credential_id: string
  kind: string
  resources: MetaResource[]
}

export function MetaResourceRenderer({ prop, properties, value, onChange, disabled }: RendererProps) {
  // By convention every meta-resource field depends on a sibling
  // `credential` property — the node spec's `dependsOn: ["credential"]`
  // is a hint to the form for refetch invalidation but the actual lookup
  // always uses the property named `credential`. Keeps each renderer
  // free of dependsOn-array parsing.
  const credentialId = readString(properties.credential)
  const kind = (prop as { resourceKind?: string }).resourceKind ?? 'page'

  const query = useQuery({
    queryKey: ['meta-resources', credentialId, kind],
    queryFn: async (): Promise<MetaResource[]> => {
      if (!credentialId) return []
      const res = await apiClient.get<MetaResourcesResponse>(API_ROUTES.META_RESOURCES, {
        params: { credential_id: credentialId, kind },
      })
      return res.data?.resources ?? []
    },
    enabled: Boolean(credentialId),
    staleTime: 1000 * 60,
  })

  const resources = useMemo(() => query.data ?? [], [query.data])
  const selected = useMemo(
    () => resources.find(r => r.id === readString(value)),
    [resources, value],
  )

  if (!credentialId) {
    return (
      <p className="text-[11.5px] text-text-faint">
        Pick a Meta account above to load {labelForKind(kind)}.
      </p>
    )
  }

  if (query.isLoading) {
    return (
      <div className="flex h-9 items-center gap-2 rounded-[7px] border border-border-faint bg-bg px-3 text-[12px] text-text-faint">
        <Loader2 size={13} className="animate-spin" />
        Loading {labelForKind(kind)}…
      </div>
    )
  }

  if (query.isError) {
    return (
      <p className="rounded-[7px] border border-err/30 bg-err/10 px-2.5 py-1.5 text-[11.5px] text-err">
        {query.error instanceof Error ? query.error.message : 'Failed to load resources.'}
      </p>
    )
  }

  if (resources.length === 0) {
    return (
      <p className="rounded-[7px] border border-dashed border-border-faint bg-bg px-2.5 py-1.5 text-[11.5px] text-text-faint">
        No {labelForKind(kind)} reachable through this Meta credential.
      </p>
    )
  }

  return (
    <div className="relative">
      <select
        value={readString(value) ?? ''}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        className={cn(
          'h-9 w-full appearance-none rounded-[7px] border border-border-faint bg-bg px-2.5 pr-7 text-[12px] text-text outline-none transition-colors',
          'hover:border-border-soft focus:border-border',
          disabled && 'opacity-50',
        )}
      >
        <option value="">Select…</option>
        {resources.map(r => (
          <option key={r.id} value={r.id}>
            {r.name}
            {r.secondary ? ` · ${r.secondary}` : ''}
          </option>
        ))}
      </select>
      <ChevronDown
        size={13}
        className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-text-faint"
      />
      {selected?.secondary && (
        <p className="mt-1 text-[10.5px] text-text-faint">{selected.secondary}</p>
      )}
    </div>
  )
}

function readString(v: unknown): string {
  if (typeof v === 'string') return v
  if (v == null) return ''
  return String(v)
}

function labelForKind(kind: string): string {
  switch (kind) {
    case 'page': return 'Pages'
    case 'ig_account': return 'Instagram accounts'
    case 'waba': return 'WhatsApp Business accounts'
    case 'waba_phone': return 'WhatsApp numbers'
    case 'lead_form': return 'Lead Ads forms'
    default: return 'resources'
  }
}

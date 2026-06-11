import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/shared/utils/apiClient'
import type { NodePropertyOption } from '../../../types/editorTypes'

function normalizeOptions(data: unknown): NodePropertyOption[] {
  // Backend `loadOptions` endpoints commonly return either a bare array or an
  // envelope `{ ok, data: [...] }` / `{ options: [...] }`. Unwrap before
  // mapping so the picker doesn't show empty for the envelope shape.
  let list: unknown = data
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const obj = data as Record<string, unknown>
    list = obj.data ?? obj.options ?? obj.items ?? obj.results ?? data
  }
  if (!Array.isArray(list)) return []
  return list.map(item => {
    if (typeof item === 'string') return { label: item, value: item }
    if (typeof item === 'object' && item !== null) {
      const obj = item as Record<string, unknown>
      return {
        label: String(obj.label ?? obj.name ?? obj.value ?? ''),
        value: obj.value ?? obj.id ?? obj.name ?? item,
        description: typeof obj.description === 'string' ? obj.description : undefined,
      }
    }
    return { label: String(item), value: item }
  })
}

/**
 * Strip a leading `/api/v1` from a loadOptions URL so the apiClient (which
 * already has that baseURL) doesn't double-prefix the request.
 */
function normalizeUrl(url: string): string {
  return url.replace(/^\/api\/v1/, '')
}

export function useLoadOptions(
  loadOptionsUrl: string | undefined,
  dependsOn: string[] | undefined,
  values: Record<string, unknown>,
) {
  // Build the params dict + a stable query-key signature in one pass.
  // The signature is a sorted string so identity changes on the `values`
  // record don't cause spurious refetches; cache misses only when an actual
  // dependent value changes.
  const { params, signature } = useMemo(() => {
    const deps = dependsOn ?? []
    const params: Record<string, string> = {}
    const parts: string[] = []
    for (const field of deps.slice().sort()) {
      const val = values[field]
      if (val !== undefined && val !== null && val !== '') {
        const s = String(val)
        params[field] = s
        parts.push(`${field}=${s}`)
      }
    }
    return { params, signature: parts.join('&') }
  }, [dependsOn, values])

  return useQuery({
    queryKey: ['load-options', loadOptionsUrl, signature] as const,
    queryFn: async (): Promise<NodePropertyOption[]> => {
      const response = await apiClient.get(normalizeUrl(loadOptionsUrl!), { params })
      return normalizeOptions(response.data)
    },
    enabled: !!loadOptionsUrl,
    staleTime: 1000 * 30,
  })
}

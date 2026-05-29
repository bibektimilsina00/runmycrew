import { useQuery } from '@tanstack/react-query'
import apiClient from '@/shared/utils/apiClient'
import type { NodePropertyOption } from '../../../types/editorTypes'

function normalizeOptions(data: unknown): NodePropertyOption[] {
  if (!Array.isArray(data)) return []
  return data.map(item => {
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

export function useLoadOptions(
  loadOptionsUrl: string | undefined,
  dependsOn: string[] | undefined,
  values: Record<string, unknown>,
) {
  const deps = dependsOn ?? []
  const params: Record<string, string> = {}
  for (const field of deps) {
    const val = values[field]
    if (val !== undefined && val !== null && val !== '') {
      params[field] = String(val)
    }
  }

  const queryKey = ['load-options', loadOptionsUrl, params] as const

  return useQuery({
    queryKey,
    queryFn: async (): Promise<NodePropertyOption[]> => {
      const response = await apiClient.get(loadOptionsUrl!, { params })
      return normalizeOptions(response.data)
    },
    enabled: !!loadOptionsUrl,
    staleTime: 1000 * 30,
  })
}

import { useQuery } from '@tanstack/react-query'
import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'

/**
 * React Query hook over `GET /tools/`. Results are stable for the editor
 * session — the catalog only changes when new tool modules are added on
 * the backend, which requires a server restart.
 */

export const ToolParamSchema = z.object({
  type: z.string(),
  required: z.boolean(),
  visibility: z.enum(['user-or-llm', 'user-only', 'llm-only', 'hidden']),
  description: z.string(),
})

export const ToolOAuthSchema = z.object({
  required: z.boolean(),
  credential_type: z.string(),
})

export const ToolRetrySchema = z.object({
  enabled: z.boolean(),
  max_retries: z.number(),
  initial_delay_ms: z.number(),
  max_delay_ms: z.number(),
})

export const ToolSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  category: z.string(),
  category_label: z.string(),
  params: z.record(z.string(), ToolParamSchema),
  oauth: ToolOAuthSchema.nullish(),
  retry: ToolRetrySchema.nullish(),
  requires_auth: z.boolean(),
})

export const ToolCategorySchema = z.object({
  id: z.string(),
  label: z.string(),
  count: z.number(),
})

export const ToolListResponseSchema = z.object({
  tools: z.array(ToolSchema),
  total: z.number(),
  categories: z.array(ToolCategorySchema),
})

export type Tool = z.infer<typeof ToolSchema>
export type ToolCategory = z.infer<typeof ToolCategorySchema>
export type ToolListResponse = z.infer<typeof ToolListResponseSchema>

export function useToolCatalog() {
  return useQuery({
    queryKey: ['tool-catalog'],
    queryFn: ({ signal }) =>
      requestJson(ToolListResponseSchema, {
        url: API_ROUTES.TOOLS_LIST,
        method: 'GET',
        signal,
      }),
    // Catalog is server-static for the editor session.
    staleTime: 1000 * 60 * 10,
  })
}

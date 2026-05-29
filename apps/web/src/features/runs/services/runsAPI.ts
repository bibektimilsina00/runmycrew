import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'

const ExecutionSchema = z.object({
  id: z.string(),
  workflow_id: z.string(),
  workflow_name: z.string(),
  workflow_color: z.string().nullable().optional(),
  status: z.string(),
  trigger_type: z.string(),
  started_at: z.string().nullable().optional(),
  finished_at: z.string().nullable().optional(),
  duration_ms: z.number().nullable().optional(),
})

const ExecutionListResponseSchema = z.object({
  executions: z.array(ExecutionSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
})

export type ApiExecution = z.infer<typeof ExecutionSchema>

export const runsAPI = {
  getAll: async (signal?: AbortSignal): Promise<z.infer<typeof ExecutionListResponseSchema>> => {
    return requestJson(ExecutionListResponseSchema, {
      url: '/executions/all',
      method: 'GET',
      params: { limit: 100 },
      signal,
    })
  },
}

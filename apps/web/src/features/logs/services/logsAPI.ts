import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'

const LogEntrySchema = z.object({
  id: z.string(),
  t: z.string(),
  lvl: z.string(),
  src: z.string(),
  msg: z.string(),
})

const LogListSchema = z.array(LogEntrySchema)

export type ApiLogEntry = z.infer<typeof LogEntrySchema>

export const logsAPI = {
  getAll: async (
    params: { limit?: number; level?: string },
    signal?: AbortSignal,
  ): Promise<ApiLogEntry[]> => {
    return requestJson(LogListSchema, {
      url: '/logs/',
      method: 'GET',
      params: {
        limit: params.limit ?? 200,
        ...(params.level ? { level: params.level } : {}),
      },
      signal,
    })
  },
}

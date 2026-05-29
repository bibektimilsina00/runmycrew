import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { ScheduleSchema } from '../types/schedulesTypes'

// Reuse workflows/with-stats, filter kind === 'schedule' on frontend
const RawSchema = z.array(
  ScheduleSchema.extend({ kind: z.string() })
)

export const schedulesAPI = {
  listAll: async (signal?: AbortSignal) => {
    const all = await requestJson(RawSchema, {
      url: API_ROUTES.WORKFLOWS_WITH_STATS, method: 'GET', signal,
    })
    return all.filter(w => w.kind === 'schedule')
  },

  validateCron: (expression: string) =>
    requestJson(
      z.object({ valid: z.boolean(), next_runs: z.array(z.string()) }),
      { url: API_ROUTES.CRON_VALIDATE, method: 'POST', data: { expression, count: 5 } }
    ),
}

import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { AutomationSchema, type WorkflowCreateRequest } from '../types/automationsTypes'

const ListSchema = z.array(AutomationSchema)

export const automationsAPI = {
  list: (signal?: AbortSignal) =>
    requestJson(ListSchema, { url: API_ROUTES.WORKFLOWS_WITH_STATS, method: 'GET', signal }),

  create: (data: WorkflowCreateRequest) =>
    requestJson(z.any(), { url: API_ROUTES.WORKFLOW_CREATE, method: 'POST', data }),

  delete: (id: string) =>
    requestJson(z.any(), { url: API_ROUTES.WORKFLOW_DELETE(id), method: 'DELETE' }),

  toggle: (id: string) =>
    requestJson(z.object({ id: z.string(), is_active: z.boolean() }), {
      url: API_ROUTES.WORKFLOW_TOGGLE(id), method: 'PATCH',
    }),

  duplicate: (id: string) =>
    requestJson(z.any(), { url: API_ROUTES.WORKFLOW_DUPLICATE(id), method: 'POST' }),

  run: (id: string) =>
    requestJson(z.object({ execution_id: z.string() }), {
      url: API_ROUTES.WORKFLOW_RUN(id), method: 'POST',
    }),
}

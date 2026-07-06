import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { LoopSchema, type LoopCreateRequest } from '../types/loopsTypes'

const ListSchema = z.array(LoopSchema)

// The create response is only consumed for its id (to navigate into the
// editor), so parse loosely but require an id.
const CreatedSchema = z.object({ id: z.string() }).passthrough()

export const loopsAPI = {
  list: (signal?: AbortSignal) =>
    requestJson(ListSchema, {
      url: `${API_ROUTES.WORKFLOWS_WITH_STATS}?kind=loop`,
      method: 'GET',
      signal,
    }),

  create: (data: LoopCreateRequest) =>
    requestJson(CreatedSchema, {
      url: API_ROUTES.WORKFLOW_CREATE,
      method: 'POST',
      data: { ...data, kind: 'loop' },
    }),

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

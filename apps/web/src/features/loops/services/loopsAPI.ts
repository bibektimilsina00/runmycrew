import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { CrewOutSchema, crewToLoop, type Loop, type LoopCreateRequest } from '../types/loopsTypes'

const CrewListSchema = z.array(CrewOutSchema)

// The create response is only consumed for its id (to navigate into the
// editor), so parse loosely but require an id.
const CreatedSchema = z.object({ id: z.string() }).passthrough()

export const loopsAPI = {
  list: async (signal?: AbortSignal): Promise<Loop[]> => {
    const crews = await requestJson(CrewListSchema, {
      url: API_ROUTES.CREWS,
      method: 'GET',
      signal,
    })
    return crews.map(crewToLoop)
  },

  create: (data: LoopCreateRequest) =>
    requestJson(CreatedSchema, {
      url: API_ROUTES.CREWS,
      method: 'POST',
      data: { name: data.name, description: data.description, graph: data.graph },
    }),

  update: (id: string, data: { name?: string; description?: string; color?: string | null }) =>
    requestJson(z.any(), {
      url: API_ROUTES.CREW_UPDATE(id),
      method: 'PUT',
      data,
    }),

  delete: (id: string) =>
    requestJson(z.any(), { url: API_ROUTES.CREW_DELETE(id), method: 'DELETE' }),

  toggle: (id: string) =>
    requestJson(z.object({ id: z.string(), is_active: z.boolean() }), {
      url: API_ROUTES.CREW_TOGGLE(id), method: 'POST', // crew toggle is POST
    }),

  duplicate: (id: string) =>
    requestJson(z.any(), { url: API_ROUTES.CREW_DUPLICATE(id), method: 'POST' }),

  run: (id: string) =>
    requestJson(z.object({ execution_id: z.string() }), {
      url: API_ROUTES.CREW_RUN(id), method: 'POST',
    }),
}

// Alias used by places that already speak "crews" instead of "loops".
export const crewsService = loopsAPI

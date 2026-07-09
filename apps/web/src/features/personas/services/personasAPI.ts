import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  PersonaSchema,
  type Persona,
  type PersonaCreateRequest,
  type PersonaUpdateRequest,
} from '../types/personaTypes'

const PersonaListSchema = z.array(PersonaSchema)

export const personasAPI = {
  list: async (signal?: AbortSignal): Promise<Persona[]> =>
    requestJson(PersonaListSchema, {
      url: API_ROUTES.PERSONAS,
      method: 'GET',
      signal,
    }),

  get: (id: string) =>
    requestJson(PersonaSchema, { url: API_ROUTES.PERSONA_GET(id), method: 'GET' }),

  create: (data: PersonaCreateRequest) =>
    requestJson(PersonaSchema, {
      url: API_ROUTES.PERSONAS,
      method: 'POST',
      data,
    }),

  update: (id: string, data: PersonaUpdateRequest) =>
    requestJson(PersonaSchema, {
      url: API_ROUTES.PERSONA_UPDATE(id),
      method: 'PATCH',
      data,
    }),

  delete: (id: string) =>
    requestJson(z.any(), { url: API_ROUTES.PERSONA_DELETE(id), method: 'DELETE' }),

  listPublic: (signal?: AbortSignal): Promise<Persona[]> =>
    requestJson(PersonaListSchema, {
      url: API_ROUTES.PERSONAS_PUBLIC,
      method: 'GET',
      signal,
    }),

  import: (sourceId: string) =>
    requestJson(PersonaSchema, {
      url: API_ROUTES.PERSONA_IMPORT(sourceId),
      method: 'POST',
    }),
}

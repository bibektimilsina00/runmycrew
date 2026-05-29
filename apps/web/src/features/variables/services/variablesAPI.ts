import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  VariableSchema,
  VariableRevealSchema,
  type VariableCreateRequest,
  type VariableUpdateRequest,
} from '../types/variablesTypes'

const VariableListSchema = z.array(VariableSchema)

export const variablesAPI = {
  list: (signal?: AbortSignal) =>
    requestJson(VariableListSchema, { url: API_ROUTES.VARIABLES_LIST, method: 'GET', signal }),

  create: (data: VariableCreateRequest) =>
    requestJson(VariableSchema, { url: API_ROUTES.VARIABLES_LIST, method: 'POST', data }),

  update: (id: string, data: VariableUpdateRequest) =>
    requestJson(VariableSchema, { url: API_ROUTES.VARIABLE(id), method: 'PUT', data }),

  delete: (id: string) =>
    requestJson(z.any(), { url: API_ROUTES.VARIABLE(id), method: 'DELETE' }),

  reveal: (id: string) =>
    requestJson(VariableRevealSchema, { url: API_ROUTES.VARIABLE_REVEAL(id), method: 'GET' }),
}

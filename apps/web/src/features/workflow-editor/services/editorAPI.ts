import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { WorkflowDetailSchema, ApiNodeDefinitionListSchema } from '../types/editorTypes'
import { z } from 'zod'

export const editorAPI = {
  getWorkflow: (id: string, signal?: AbortSignal) =>
    requestJson(WorkflowDetailSchema, {
      url: API_ROUTES.WORKFLOW_GET(id),
      method: 'GET',
      signal,
    }),

  saveGraph: (id: string, graph: object, expectedVersion?: number) =>
    requestJson(WorkflowDetailSchema, {
      url: API_ROUTES.WORKFLOW_UPDATE(id),
      method: 'PUT',
      data: { graph, expected_version: expectedVersion },
    }),

  rename: (id: string, name: string) =>
    requestJson(WorkflowDetailSchema, {
      url: API_ROUTES.WORKFLOW_UPDATE(id),
      method: 'PUT',
      data: { name },
    }),

  toggleActive: (id: string) =>
    requestJson(z.object({ id: z.string(), is_active: z.boolean() }), {
      url: API_ROUTES.WORKFLOW_TOGGLE(id),
      method: 'PATCH',
    }),

  run: (id: string) =>
    requestJson(z.object({ execution_id: z.string() }), {
      url: API_ROUTES.WORKFLOW_RUN(id),
      method: 'POST',
    }),

  getNodeDefinitions: (signal?: AbortSignal) =>
    requestJson(ApiNodeDefinitionListSchema, {
      url: API_ROUTES.NODES_LIST,
      method: 'GET',
      signal,
    }),
}

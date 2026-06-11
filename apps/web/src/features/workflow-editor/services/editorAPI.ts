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

  /**
   * Execute a single node in isolation with the supplied properties + input
   * payload. Synchronous: returns the node's output (or error) when finished.
   * Pass `signal` from an `AbortController` to cancel the run.
   */
  testNode: (
    body: {
      node_type: string
      properties: Record<string, unknown>
      input_data?: Record<string, unknown>
      workflow_id?: string
    },
    signal?: AbortSignal,
  ) =>
    requestJson(NodeTestResponseSchema, {
      url: API_ROUTES.NODE_TEST,
      method: 'POST',
      data: body,
      signal,
    }),
}

export const NodeTestResponseSchema = z.object({
  success: z.boolean(),
  output: z.union([z.record(z.string(), z.unknown()), z.array(z.unknown())]).nullable().optional(),
  error: z.string().nullable().optional(),
  logs: z.array(z.record(z.string(), z.unknown())).default([]),
  duration_ms: z.number(),
})
export type NodeTestResponse = z.infer<typeof NodeTestResponseSchema>

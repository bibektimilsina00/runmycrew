import { requestJson } from '@/shared/utils/apiClient'
import {
  WorkflowSchema,
  WorkflowWithStatsSchema,
  type Workflow,
  type WorkflowBatchUpdate,
} from '../types/workflowTypes'
import { z } from 'zod'

export const workflowAPI = {
  list: (signal?: AbortSignal) =>
    requestJson(z.array(WorkflowSchema), { url: '/workflows/', method: 'GET', signal }),

  listWithStats: (signal?: AbortSignal) =>
    requestJson(z.array(WorkflowWithStatsSchema), { url: '/workflows/with-stats', method: 'GET', signal }),

  create: (data: { name: string; folderId?: string | null; position?: number; color?: string | null }) =>
    requestJson(WorkflowSchema, {
      url: '/workflows/',
      method: 'POST',
      data: {
        name: data.name,
        folder_id: data.folderId,
        position: data.position ?? 0,
        color: data.color,
      },
    }),

  update: (id: string, data: Partial<Workflow> & { expected_version?: number }) =>
    requestJson(WorkflowSchema, {
      url: `/workflows/${id}`,
      method: 'PUT',
      data,
    }),

  duplicate: (id: string) =>
    requestJson(WorkflowSchema, {
      url: `/workflows/${id}/duplicate`,
      method: 'POST',
    }),

  delete: (id: string) =>
    requestJson(z.any(), {
      url: `/workflows/${id}`,
      method: 'DELETE',
    }),

  batchUpdate: (data: WorkflowBatchUpdate) =>
    requestJson(z.any(), {
      url: '/workflows/batch',
      method: 'PATCH',
      data,
    }),
}

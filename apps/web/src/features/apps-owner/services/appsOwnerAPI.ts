import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  AnalyticsOverviewSchema,
  PublishedAppOutSchema,
  type AnalyticsOverview,
  type PublishedApp,
  type PublishAppRequest,
} from '../types/appsOwnerTypes'

const OptionalApp = z.union([PublishedAppOutSchema, z.null()])

export const appsOwnerAPI = {
  publish: (workflowId: string, data: PublishAppRequest): Promise<PublishedApp> =>
    requestJson(PublishedAppOutSchema, {
      url: API_ROUTES.WORKFLOW_PUBLISH(workflowId),
      method: 'POST',
      data,
    }),

  unpublish: (workflowId: string): Promise<null> =>
    requestJson(z.any(), {
      url: API_ROUTES.WORKFLOW_PUBLISH(workflowId),
      method: 'DELETE',
    }),

  current: (workflowId: string): Promise<PublishedApp | null> =>
    requestJson(OptionalApp, {
      url: API_ROUTES.WORKFLOW_APP(workflowId),
      method: 'GET',
    }),

  versions: (workflowId: string): Promise<PublishedApp[]> =>
    requestJson(z.array(PublishedAppOutSchema), {
      url: API_ROUTES.WORKFLOW_APP_VERSIONS(workflowId),
      method: 'GET',
    }),

  rollback: (workflowId: string, body: { version_num: number }): Promise<PublishedApp> =>
    requestJson(PublishedAppOutSchema, {
      url: `${API_ROUTES.WORKFLOW_APP(workflowId)}/rollback`,
      method: 'POST',
      data: body,
    }),

  resetApiKey: (workflowId: string): Promise<{ api_key: string }> =>
    requestJson(z.object({ api_key: z.string() }), {
      url: `${API_ROUTES.WORKFLOW_APP(workflowId)}/reset-api-key`,
      method: 'POST',
    }),

  analytics: (workflowId: string): Promise<AnalyticsOverview> =>
    requestJson(AnalyticsOverviewSchema, {
      url: `${API_ROUTES.WORKFLOW_APP(workflowId)}/analytics`,
      method: 'GET',
    }),
}

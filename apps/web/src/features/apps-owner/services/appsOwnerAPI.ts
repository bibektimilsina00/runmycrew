import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  PublishedAppOutSchema,
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
}

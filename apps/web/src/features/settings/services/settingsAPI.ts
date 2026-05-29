import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { ApiKeySchema, UserProfileSchema } from '../types/settingsTypes'

export const settingsAPI = {
  updateProfile: (fullName?: string, password?: string) =>
    requestJson(UserProfileSchema, {
      url: API_ROUTES.USER_ME,
      method: 'PUT',
      data: { full_name: fullName, password: password || undefined },
    }),

  getApiKeys: (signal?: AbortSignal) =>
    requestJson(z.array(ApiKeySchema), {
      url: API_ROUTES.USER_API_KEYS,
      method: 'GET',
      signal,
    }),

  createApiKey: (name: string) =>
    requestJson(ApiKeySchema, {
      url: API_ROUTES.USER_API_KEYS,
      method: 'POST',
      data: { name },
    }),

  revokeApiKey: (id: string) =>
    requestJson(z.any(), {
      url: API_ROUTES.USER_API_KEY(id),
      method: 'DELETE',
    }),
}

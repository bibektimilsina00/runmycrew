import axios, { type AxiosRequestConfig } from 'axios'
import { z } from 'zod'
import { useAuthStore } from '@/stores/auth-store'
import { useWorkspaceStore } from '@/stores/workspace-store'
import { logger } from '@/lib/logger'

/**
 * Fuse API Client
 */

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Inject Auth Token + Workspace context into every request
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  } else {
    // Fallback to localStorage (for cold starts)
    try {
      const storage = localStorage.getItem('fuse-auth-storage')
      if (storage) {
        const { state } = JSON.parse(storage)
        if (state.token) config.headers.Authorization = `Bearer ${state.token}`
      }
    } catch { /* silent */ }
  }

  // Inject workspace context — all scoped API calls need this
  const workspaceId = useWorkspaceStore.getState().currentWorkspaceId
  if (workspaceId) {
    config.headers['X-Workspace-ID'] = workspaceId
  }

  return config
})

/**
 * Perform a type-safe API request and validate the response against a Zod schema.
 * 
 * @param schema - The Zod schema to validate the response against
 * @param config - Axios request configuration
 * @returns The validated and typed response data
 */
export async function requestJson<T>(
  schema: z.ZodSchema<T>,
  config: AxiosRequestConfig
): Promise<T> {
  const response = await apiClient.request(config)
  
  // Validate the response against the provided schema
  const result = schema.safeParse(response.data)
  
  if (!result.success) {
    logger.error('API Response Validation Failed:', result.error)
    throw new Error('API contract violation: The server returned an unexpected response format.')
  }
  
  return result.data
}

export default apiClient

import axios, { type AxiosRequestConfig } from 'axios'
import { z } from 'zod'
import { useAuthStore } from '@/features/auth/store/authStore'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import { logger } from '@/shared/utils/logger'

/**
 * Custom error class for API errors, carrying response status and details.
 */
export class APIError extends Error {
  status?: number
  detail?: string

  constructor(message: string, status?: number, detail?: string) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.detail = detail
  }
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Inject Auth Token into every request
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  } else {
    // Fallback to localStorage (for cold starts)
    try {
      const storageToken = localStorage.getItem('fuse-auth-token')
      if (storageToken) {
        config.headers.Authorization = `Bearer ${storageToken}`
      }
    } catch {
      // Ignore private browsing storage errors
    }
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
  try {
    const response = await apiClient.request(config)
    
    // Validate the response against the provided schema
    const result = schema.safeParse(response.data)
    
    if (!result.success) {
      logger.error('API Response Validation Failed:', result.error)
      throw new APIError('API contract violation: The server returned an unexpected response format.')
    }
    
    return result.data
  } catch (err: unknown) {
    if (axios.isAxiosError(err)) {
      const status = err.response?.status
      let detail = 'An unexpected error occurred'
      const responseData = err.response?.data
      
      // If we got a JSON response, parse the error details
      if (responseData && typeof responseData === 'object' && !Array.isArray(responseData)) {
        const errorData = responseData as Record<string, unknown>
        if (typeof errorData.detail === 'string') {
          detail = errorData.detail
        } else if (errorData.detail && typeof errorData.detail === 'object') {
          detail = JSON.stringify(errorData.detail)
        } else if (typeof errorData.message === 'string') {
          detail = errorData.message
        }
      } else if (status === 504 || status === 502) {
        detail = 'Could not connect to the backend server. Please verify that the API server is running.'
      } else if (typeof responseData === 'string' && responseData.trim()) {
        // If it's a plain string or HTML error, try to extract a clean message
        if (responseData.includes('Gateway Timeout') || responseData.includes('504')) {
          detail = 'Gateway Timeout: The API server is not responding.'
        } else if (responseData.includes('Bad Gateway') || responseData.includes('502')) {
          detail = 'Bad Gateway: The API server is offline.'
        } else {
          // Truncate to avoid dumping a huge HTML page into the UI
          detail = responseData.length > 100 ? `${responseData.substring(0, 100)}...` : responseData
        }
      } else if (err.message) {
        detail = err.message
      }
      
      throw new APIError(detail, status, detail)
    }
    throw err
  }
}

export default apiClient

import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { CredentialSchema, ProviderSchema, OAuthUrlSchema, AuditLogSchema } from '../types/connectionsTypes'

const CredentialListSchema = z.array(CredentialSchema)
const ProviderListSchema   = z.array(ProviderSchema)

export const connectionsAPI = {
  listCredentials: (signal?: AbortSignal) =>
    requestJson(CredentialListSchema, { url: API_ROUTES.CREDENTIALS, method: 'GET', signal }),

  listProviders: (signal?: AbortSignal) =>
    requestJson(ProviderListSchema, { url: API_ROUTES.CREDENTIAL_PROVIDERS, method: 'GET', signal }),

  createCredential: (data: { name: string; type: string; data: Record<string, string> }) =>
    requestJson(CredentialSchema, { url: API_ROUTES.CREDENTIALS, method: 'POST', data }),

  renameCredential: (id: string, name: string) =>
    requestJson(CredentialSchema, { url: API_ROUTES.CREDENTIAL(id), method: 'PATCH', data: { name } }),

  deleteCredential: (id: string) =>
    requestJson(z.any(), { url: API_ROUTES.CREDENTIAL(id), method: 'DELETE' }),

  getOAuthUrl: (service: string, name?: string) =>
    requestJson(OAuthUrlSchema, {
      url: API_ROUTES.CREDENTIAL_OAUTH_URL(service),
      method: 'GET',
      params: name ? { name } : undefined,
    }),

  listAuditLog: (signal?: AbortSignal) =>
    requestJson(z.array(AuditLogSchema), { url: API_ROUTES.CREDENTIAL_AUDIT, method: 'GET', signal }),
}

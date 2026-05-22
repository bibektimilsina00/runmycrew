/**
 * Centralized Application Routes (Frontend)
 */
export const APP_ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  DASHBOARD: '/dashboard',
  SETTINGS: '/settings',
  SHOWCASE: '/showcase',
  AUTOMATIONS: '/automations',
  TEMPLATES: '/templates',
  RUNS: '/runs',
  SCHEDULES: '/schedules',
  LOGS: '/logs',
  TABLES: '/tables',
  FILES: '/files',
  KNOWLEDGE: '/knowledge',
  KNOWLEDGE_DETAIL: (id: string) => `/knowledge/${id}`,
  KNOWLEDGE_DOCUMENT: (kbId: string, docId: string) => `/knowledge/${kbId}/documents/${docId}`,
  KB_CHUNKS: (kbId: string, docId: string) => `/kb/${kbId}/documents/${docId}/chunks`,
  KB_CHUNK: (kbId: string, chunkId: string) => `/kb/${kbId}/chunks/${chunkId}`,
  VARIABLES: '/variables',
  CONNECTIONS: '/connections',
  WORKSPACE_SETTINGS: '/settings/workspace',
  INVITE_ACCEPT: '/invite/:token',
  WORKFLOW_DETAIL: '/workflows/:id',
  WORKFLOW: (id: string) => `/workflows/${id}`,
} as const

export type AppRoute = typeof APP_ROUTES[keyof typeof APP_ROUTES]

/**
 * Centralized API Routes (Backend Endpoints relative to base url '/api/v1')
 */
export const API_ROUTES = {
  // Auth
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  ME: '/auth/me',
  FORGOT_PASSWORD: '/auth/forgot-password',
  RESET_PASSWORD: '/auth/reset-password',

  // Connections (credentials)
  CREDENTIALS: '/credentials/',
  CREDENTIAL: (id: string) => `/credentials/${id}`,
  CREDENTIAL_PROVIDERS: '/credentials/providers',
  CREDENTIAL_OAUTH_URL: (service: string) => `/credentials/oauth/${service}/url`,
  CREDENTIAL_AUDIT: '/credentials/audit',

  // Knowledge base
  KB_LIST: '/kb/',
  KB: (id: string) => `/kb/${id}`,
  KB_DOCS: (id: string) => `/kb/${id}/documents`,
  KB_DOC_TEXT: (id: string) => `/kb/${id}/documents/text`,
  KB_DOC_UPLOAD: (id: string) => `/kb/${id}/documents/upload`,
  KB_DOC_URL: (id: string) => `/kb/${id}/documents/url`,
  KB_DOC: (kbId: string, docId: string) => `/kb/${kbId}/documents/${docId}`,
  KB_DOC_REINDEX: (kbId: string, docId: string) => `/kb/${kbId}/documents/${docId}/reindex`,
  KB_CHUNKS: (kbId: string, docId: string) => `/kb/${kbId}/documents/${docId}/chunks`,
  KB_CHUNK: (kbId: string, chunkId: string) => `/kb/${kbId}/chunks/${chunkId}`,
  KB_SEARCH: (id: string) => `/kb/${id}/search`,
  KB_REINDEX: (id: string) => `/kb/${id}/reindex`,

  // Variables (backed by /secrets endpoint)
  VARIABLES_LIST: '/secrets/',
  VARIABLE: (id: string) => `/secrets/${id}`,
  VARIABLE_REVEAL: (id: string) => `/secrets/${id}/reveal`,

  // Files / assets
  ASSETS: '/assets/',
  ASSET_STATS: '/assets/stats',
  ASSET_UPLOAD: '/assets/upload',
  ASSET: (id: string) => `/assets/${id}`,
  ASSET_VIEW: (id: string) => `/assets/${id}/view`,
  ASSET_DOWNLOAD: (id: string) => `/assets/${id}/download`,

  // User / Account
  USER_ME: '/users/me',
  USER_API_KEYS: '/users/api-keys',
  USER_API_KEY: (id: string) => `/users/api-keys/${id}`,

  // Workspaces
  WORKSPACES: '/workspaces/',
  WORKSPACE: (id: string) => `/workspaces/${id}`,
  WORKSPACE_UPDATE: (id: string) => `/workspaces/${id}`,
  WORKSPACE_DELETE: (id: string) => `/workspaces/${id}`,
  WORKSPACE_MEMBERS: (id: string) => `/workspaces/${id}/members`,
  WORKSPACE_MEMBER: (workspaceId: string, userId: string) => `/workspaces/${workspaceId}/members/${userId}`,
  WORKSPACE_INVITES: (id: string) => `/workspaces/${id}/invites`,
  INVITE_PREVIEW: (token: string) => `/workspaces/invites/${token}`,
  INVITE_ACCEPT: (token: string) => `/workspaces/invites/${token}/accept`,
} as const

export type ApiRoute = typeof API_ROUTES[keyof typeof API_ROUTES]

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
  VARIABLES: '/variables',
  CONNECTIONS: '/connections',
  WORKSPACE_SETTINGS: '/settings/workspace',
  INVITE_ACCEPT: '/invite/:token',
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

  // Workspaces
  WORKSPACES: '/workspaces/',
  WORKSPACE: (id: string) => `/workspaces/${id}`,
  WORKSPACE_MEMBERS: (id: string) => `/workspaces/${id}/members`,
  WORKSPACE_MEMBER: (workspaceId: string, userId: string) => `/workspaces/${workspaceId}/members/${userId}`,
  WORKSPACE_INVITES: (id: string) => `/workspaces/${id}/invites`,
  INVITE_PREVIEW: (token: string) => `/workspaces/invites/${token}`,
  INVITE_ACCEPT: (token: string) => `/workspaces/invites/${token}/accept`,
} as const

export type ApiRoute = typeof API_ROUTES[keyof typeof API_ROUTES]

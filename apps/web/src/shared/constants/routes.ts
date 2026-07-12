/**
 * External URLs (marketing site, docs, etc.).
 * Overridable via ``VITE_DOCS_URL`` / ``VITE_MARKETING_URL`` so dev
 * points at localhost:3100 while prod hits the deployed marketing site.
 */
export const EXTERNAL_URLS = {
  DOCS: import.meta.env.VITE_DOCS_URL || 'https://runmycrew.com/docs',
  MARKETING: import.meta.env.VITE_MARKETING_URL || 'https://runmycrew.com',
  FEEDBACK: import.meta.env.VITE_FEEDBACK_URL || 'https://runmycrew.com/feedback',
} as const

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
  PERSONAS: '/loops/personas',
  PERSONA_NEW: '/loops/personas/new',
  PERSONA_EDIT: (id: string) => `/loops/personas/${id}`,
  CREW_TEMPLATES: '/loops/templates',
  TEMPLATES: '/templates',
  TEMPLATE_DETAIL: (slug: string) => `/templates/${slug}`,
  MY_TEMPLATES: '/templates/mine',
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
  SKILLS: '/skills',
  SKILL_EDIT: (id: string) => `/skills/${id}`,
  SKILL_NEW: '/skills/new',
  VARIABLES: '/variables',
  CONNECTIONS: '/connections',
  WORKSPACE_SETTINGS: '/settings/workspace',
  INVITE_ACCEPT: '/invites/:token',
  WORKFLOW_DETAIL: '/workflows/:id',
  WORKFLOW: (id: string) => `/workflows/${id}`,
  CREW_EDITOR: (id: string) => `/crews/${id}`,
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

  // Nodes
  NODES_LIST: '/nodes/',
  NODE_TEST:  '/nodes/test',

  // Tools (agent catalog)
  TOOLS_LIST: '/tools/',
  TOOLS_WORKFLOWS: '/tools/workflows',
  TOOLS_MCP_PROBE: '/tools/mcp/probe',

  // Meta — resource discovery (Pages, IG accounts, WABA, Lead forms)
  META_RESOURCES: '/meta/resources',
  META_WA_TEMPLATES: '/meta/wa/templates',

  // Workflows / Automations
  WORKFLOWS_WITH_STATS: '/workflows/with-stats',
  WORKFLOW_CREATE: '/workflows/',
  WORKFLOW_GET: (id: string) => `/workflows/${id}`,
  WORKFLOW_UPDATE: (id: string) => `/workflows/${id}`,
  WORKFLOW_DELETE: (id: string) => `/workflows/${id}`,
  WORKFLOW_TOGGLE: (id: string) => `/workflows/${id}/toggle`,
  WORKFLOW_DUPLICATE: (id: string) => `/workflows/${id}/duplicate`,
  WORKFLOW_RUN: (id: string) => `/workflows/${id}/run`,

  // Crews (dedicated /crews backend — replaces the old kind=loop workflow hack)
  CREWS: '/crews/',
  CREW_GET: (id: string) => `/crews/${id}`,
  CREW_UPDATE: (id: string) => `/crews/${id}`,
  CREW_DELETE: (id: string) => `/crews/${id}`,
  CREW_TOGGLE: (id: string) => `/crews/${id}/toggle`,
  CREW_DUPLICATE: (id: string) => `/crews/${id}/duplicate`,
  CREW_RUN: (id: string) => `/crews/${id}/run`,
  CREW_EXECUTIONS: (id: string) => `/crews/${id}/executions`,

  // Chat-app owner endpoints — password / api_key / analytics under
  // /workflows/{id}/app. (No publish endpoint — activating the workflow
  // is enough.)
  WORKFLOW_APP_PASSWORD: (id: string) => `/workflows/${id}/app/password`,
  WORKFLOW_APP_RESET_API_KEY: (id: string) => `/workflows/${id}/app/reset-api-key`,
  WORKFLOW_APP_ANALYTICS: (id: string) => `/workflows/${id}/app/analytics`,
  WORKFLOW_APP_SESSIONS: (id: string) => `/workflows/${id}/app/sessions`,

  // Personas (reusable named agents that overlay onto action.agent nodes)
  PERSONAS: '/personas/',
  PERSONA_GET: (id: string) => `/personas/${id}`,
  PERSONA_UPDATE: (id: string) => `/personas/${id}`,
  PERSONA_DELETE: (id: string) => `/personas/${id}`,
  PERSONAS_PUBLIC: '/personas/public',
  PERSONA_IMPORT: (sourceId: string) => `/personas/import/${sourceId}`,

  DASHBOARD_STATS: '/dashboard/stats',
  CRON_VALIDATE: '/cron/validate',
  CRON_NEXT_RUNS: '/cron/next-runs',

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
  KB_EMBEDDING_MODELS: '/kb/embedding-models',

  // Skills (agent skills — markdown bodies loaded on-demand via load_skill tool)
  SKILLS_LIST: '/skills/',
  SKILL: (id: string) => `/skills/${id}`,
  SKILL_CREATE: '/skills/',

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

  // Tables
  TABLES_LIST: '/tables/',
  TABLES_IMPORT_CSV: '/tables/import.csv',
  TABLE: (id: string) => `/tables/${id}`,
  TABLE_COLUMNS: (id: string) => `/tables/${id}/columns`,
  TABLE_COLUMN: (tableId: string, columnId: string) => `/tables/${tableId}/columns/${columnId}`,
  TABLE_ROWS: (id: string) => `/tables/${id}/rows`,
  TABLE_ROW: (tableId: string, rowId: string) => `/tables/${tableId}/rows/${rowId}`,
  TABLE_IMPORT_ROWS_CSV: (id: string) => `/tables/${id}/import.csv`,
  TABLE_EXPORT_CSV: (id: string) => `/tables/${id}/export.csv`,

  // User / Account
  USER_ME: '/users/me',
  // Backend mounts the api-keys router at /api-keys (not under /users) —
  // the old /users/api-keys path 404'd, so Settings → API keys was dead.
  USER_API_KEYS: '/api-keys',
  USER_API_KEY: (id: string) => `/api-keys/${id}`,

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

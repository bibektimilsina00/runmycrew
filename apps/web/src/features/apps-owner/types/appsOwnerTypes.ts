import { z } from 'zod'

export const PublishedAppOutSchema = z.object({
  id: z.string(),
  workspace_id: z.string(),
  workflow_id: z.string(),
  published_by: z.string(),
  app_slug: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  mode: z.string(),
  version_num: z.number(),
  config: z.record(z.string(), z.any()),
  auth_mode: z.string(),
  is_active: z.boolean(),
  published_at: z.string(),
  updated_at: z.string(),
  expires_at: z.string().nullable(),
  public_url: z.string().nullable().optional(),
  // Backend never sends the raw hash — but the presence is inferred by
  // an owner-visible `has_password` / `has_api_key` flag on the same row.
  password_hash: z.string().nullable().optional(),
  api_key_hash: z.string().nullable().optional(),
})
export type PublishedApp = z.infer<typeof PublishedAppOutSchema>

export const AnalyticsOverviewSchema = z.object({
  total_sessions: z.number(),
  total_messages: z.number(),
  total_cost_usd: z.number(),
  active_today: z.number(),
  messages_today: z.number(),
  cost_today: z.number(),
  top_prompts: z.array(z.object({ prompt: z.string(), count: z.number() })),
  session_cost_p50: z.number(),
  session_cost_p95: z.number(),
})
export type AnalyticsOverview = z.infer<typeof AnalyticsOverviewSchema>

export interface PublishAppRequest {
  app_slug?: string
  title?: string
  description?: string
  mode?: string
  config?: Record<string, unknown>
  auth_mode?: string
  password?: string
  expires_at?: string | null
}

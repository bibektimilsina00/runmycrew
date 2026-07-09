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
})
export type PublishedApp = z.infer<typeof PublishedAppOutSchema>

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

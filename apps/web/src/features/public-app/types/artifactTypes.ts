import { z } from 'zod'

/**
 * Mirror of the backend Artifact enum. Frontend picks a renderer by `type`;
 * `data` shape is type-specific and validated per-renderer.
 */
export const ArtifactSchema = z.object({
  id: z.string(),
  type: z.string(),
  title: z.string().nullable().optional(),
  data: z.record(z.string(), z.any()).default({}),
  metadata: z.record(z.string(), z.any()).default({}),
  render_hint: z.string().nullable().optional(),
  created_at: z.string().optional(),
})

export type Artifact = z.infer<typeof ArtifactSchema>

export const ARTIFACT_TYPES = [
  'markdown',
  'code',
  'image',
  'url_preview',
  'iframe',
  'html',
  'file',
  'audio',
  'video',
  'json',
  'table',
  'chart',
  'citation',
  'pdf',
] as const

export type ArtifactType = (typeof ARTIFACT_TYPES)[number]

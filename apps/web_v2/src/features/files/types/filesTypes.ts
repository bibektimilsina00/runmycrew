import { z } from 'zod'

export const FileSourceSchema = z.enum(['uploaded', 'generated', 'attachment'])
export type FileSource = z.infer<typeof FileSourceSchema>

export const FileAssetSchema = z.object({
  id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  user_id: z.string().uuid(),
  name: z.string(),
  file_type: z.string(),
  file_size: z.number().int().nonnegative(),
  source_type: FileSourceSchema,
  created_at: z.string(),
  updated_at: z.string(),
  url: z.string(),
  download_url: z.string(),
})
export type FileAsset = z.infer<typeof FileAssetSchema>

export const FileStatsSchema = z.object({
  count: z.number().int().nonnegative(),
  total_size: z.number().int().nonnegative(),
})
export type FileStats = z.infer<typeof FileStatsSchema>

export type FileFilter = 'all' | FileSource | 'attachments'
export type FileSort = 'created_desc' | 'name_asc' | 'size_desc'

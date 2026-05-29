import { z } from 'zod'

export const FolderSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  parent_id: z.string().uuid().optional().nullable(),
  user_id: z.string().uuid().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Folder = z.infer<typeof FolderSchema>

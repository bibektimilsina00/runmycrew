import { z } from 'zod'

export const ApiKeySchema = z.object({
  id: z.string(),
  name: z.string(),
  key_preview: z.string(),
  created_at: z.string(),
  token: z.string().optional(),
})

export type ApiKey = z.infer<typeof ApiKeySchema>

export const UserProfileSchema = z.object({
  id: z.string(),
  email: z.string(),
  full_name: z.string().nullable().optional(),
  avatar_url: z.string().nullable().optional(),
  is_active: z.boolean(),
  created_at: z.string(),
})

export type UserProfile = z.infer<typeof UserProfileSchema>

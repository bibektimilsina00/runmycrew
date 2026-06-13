import { z } from 'zod'

/**
 * Server shape — mirrors `apps/api/app/features/skills/schemas.py`.
 *
 * The backend still has a `color` column for legacy reasons; we accept
 * it as an optional field so old payloads still parse, but the UI no
 * longer exposes or sends it.
 */
export const SkillSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  icon: z.string(),
  color: z.string().optional(),
  content: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
})

/** Lightweight metadata returned by `GET /skills/` — the list view only
 *  needs name/description/icon; the full content blob is fetched
 *  per-skill when the editor opens. */
export const SkillMetaSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  icon: z.string(),
  color: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})

export const SkillCreateSchema = z.object({
  name: z.string().min(1).max(64),
  description: z.string().max(1024).default(''),
  icon: z.string().max(64).default('BookOpen'),
  content: z.string().default(''),
})

export const SkillUpdateSchema = SkillCreateSchema.partial()

export type Skill = z.infer<typeof SkillSchema>
export type SkillMeta = z.infer<typeof SkillMetaSchema>
export type SkillCreate = z.infer<typeof SkillCreateSchema>
export type SkillUpdate = z.infer<typeof SkillUpdateSchema>

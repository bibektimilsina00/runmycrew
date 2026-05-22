import { z } from 'zod'

export const VariableScopeSchema = z.enum(['workspace', 'personal'])
export type VariableScope = z.infer<typeof VariableScopeSchema>

export const VariableSchema = z.object({
  id: z.string(),
  name: z.string(),              // KEY name (UPPER_SNAKE_CASE)
  value: z.string().nullable(),  // null for secrets — not returned in list
  scope: VariableScopeSchema,
  is_secret: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type Variable = z.infer<typeof VariableSchema>

export const VariableRevealSchema = z.object({
  id: z.string(),
  name: z.string(),
  value: z.string(),
})
export type VariableReveal = z.infer<typeof VariableRevealSchema>

export interface VariableCreateRequest {
  name: string
  value: string
  scope: VariableScope
  is_secret: boolean
}

export interface VariableUpdateRequest {
  name?: string
  value?: string
  scope?: VariableScope
  is_secret?: boolean
}

import { z } from 'zod'

// A "loop" is a workflow whose backend `kind === 'loop'` — an autonomous AI
// agent that runs in a verified loop. It reuses the same list/stats shape as
// automations; the `kind` field on the list row (flow/agent/schedule) is a
// separate display concept and is intentionally unrelated to the workflow's
// automation-vs-loop kind.
export const LoopKindSchema   = z.enum(['flow', 'agent', 'schedule'])
export const LoopStatusSchema = z.enum(['active', 'paused', 'error', 'draft'])
export type LoopKind   = z.infer<typeof LoopKindSchema>
export type LoopStatus = z.infer<typeof LoopStatusSchema>

export const LoopSchema = z.object({
  id:              z.string().uuid(),
  name:            z.string(),
  description:     z.string().nullable().optional(),
  is_active:       z.boolean(),
  color:           z.string().nullable().optional(),
  folder_id:       z.string().nullable().optional(),
  workspace_id:    z.string(),
  user_id:         z.string(),
  created_at:      z.string(),
  updated_at:      z.string(),
  kind:            LoopKindSchema,
  trigger:         z.string(),
  status:          LoopStatusSchema,
  execution_count: z.number(),
  last_run:        z.string().nullable().optional(),
  last_run_status: z.string().nullable().optional(),
})
export type Loop = z.infer<typeof LoopSchema>

export interface LoopCreateRequest {
  name: string
  description?: string
  folder_id?: string | null
  color?: string | null
}

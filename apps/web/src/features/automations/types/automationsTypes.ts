import { z } from 'zod'

export const WorkflowKindSchema   = z.enum(['flow', 'agent', 'schedule'])
export const WorkflowStatusSchema = z.enum(['active', 'paused', 'error', 'draft'])
export type WorkflowKind   = z.infer<typeof WorkflowKindSchema>
export type WorkflowStatus = z.infer<typeof WorkflowStatusSchema>

export const AutomationSchema = z.object({
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
  kind:            WorkflowKindSchema,
  trigger:         z.string(),
  status:          WorkflowStatusSchema,
  execution_count: z.number(),
  last_run:        z.string().nullable().optional(),
  last_run_status: z.string().nullable().optional(),
})
export type Automation = z.infer<typeof AutomationSchema>

export interface WorkflowCreateRequest {
  name: string
  description?: string
  folder_id?: string | null
  color?: string | null
}

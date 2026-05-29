import { z } from 'zod'

export const ScheduleStatusSchema = z.enum(['active', 'paused', 'error', 'draft'])
export type ScheduleStatus = z.infer<typeof ScheduleStatusSchema>

export const ScheduleSchema = z.object({
  id:              z.string().uuid(),
  name:            z.string(),
  description:     z.string().nullable().optional(),
  is_active:       z.boolean(),
  color:           z.string().nullable().optional(),
  workspace_id:    z.string(),
  user_id:         z.string(),
  created_at:      z.string(),
  updated_at:      z.string(),
  // computed by backend
  status:          ScheduleStatusSchema,
  execution_count: z.number(),
  last_run:        z.string().nullable().optional(),
  last_run_status: z.string().nullable().optional(),
  // schedule-specific
  cron_expression: z.string().nullable().optional(),
  timezone:        z.string().nullable().optional(),
  next_run:        z.string().nullable().optional(),
})
export type Schedule = z.infer<typeof ScheduleSchema>

import { z } from 'zod'

export const WorkflowSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  folder_id: z.string().uuid().optional().nullable(),
  name: z.string().min(1),
  description: z.string().optional().nullable(),
  schema_version: z.string().optional(),
  graph: z.any().optional(),
  is_active: z.boolean(),
  position: z.number().int().optional().default(0),
  color: z.string().optional().nullable(),
  env: z.record(z.string(), z.string()).optional().nullable(),
  version_vector: z.number().int().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Workflow = z.infer<typeof WorkflowSchema>

export const WorkflowWithStatsSchema = WorkflowSchema.extend({
  execution_count: z.number().int().optional(),
})

export type WorkflowWithStats = z.infer<typeof WorkflowWithStatsSchema>

export const WorkflowBatchItemSchema = z.object({
  id: z.string().uuid(),
  folder_id: z.string().uuid().optional().nullable(),
  position: z.number().int().optional().nullable(),
  color: z.string().optional().nullable(),
})

export const WorkflowBatchUpdateSchema = z.object({
  updates: z.array(WorkflowBatchItemSchema),
})

export type WorkflowBatchUpdate = z.infer<typeof WorkflowBatchUpdateSchema>

export const CURATED_COLORS = [
  '#6366f1', // Indigo
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#f43f5e', // Rose
  '#0ea5e9', // Sky
  '#8b5cf6', // Violet
  '#ec4899', // Pink
  '#3b82f6', // Blue
]

/**
 * Gets the color for a workflow, falling back to a deterministic premium color based on ID if color is not set.
 */
export function getWorkflowColor(workflow: { id?: string; color?: string | null }): string {
  if (workflow.color) return workflow.color
  let hash = 0
  const idStr = workflow.id || 'default'
  for (let i = 0; i < idStr.length; i++) {
    hash = idStr.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % CURATED_COLORS.length
  return CURATED_COLORS[index]
}



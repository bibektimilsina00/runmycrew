import { z } from 'zod'

/**
 * Helper to define a standard API contract.
 * Used to keep frontend and backend schemas in sync.
 */
export function defineRouteContract<
  TBody extends z.ZodTypeAny = z.ZodTypeAny,
  TResponse extends z.ZodTypeAny = z.ZodTypeAny
>(contract: {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  path: string
  body?: TBody
  response: TResponse
}) {
  return contract
}

// Example contract: Workflow
export const WorkflowSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid().optional(),
  name: z.string().min(1),
  description: z.string().optional().nullable(),
  schema_version: z.string().optional(),
  is_active: z.boolean().optional(),
  status: z.string().optional(),
  folder_id: z.string().uuid().optional().nullable(),
  position: z.number().optional(),
  color: z.string().optional().nullable(),
  graph: z.any().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Workflow = z.infer<typeof WorkflowSchema>

export const WorkflowBatchItemSchema = z.object({
  id: z.string().uuid(),
  folder_id: z.string().uuid().optional().nullable(),
  position: z.number().optional().nullable(),
  color: z.string().optional().nullable(),
})

export const WorkflowBatchUpdateSchema = z.object({
  updates: z.array(WorkflowBatchItemSchema),
})

export type WorkflowBatchUpdate = z.infer<typeof WorkflowBatchUpdateSchema>

export const FolderSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1),
  parent_id: z.string().uuid().optional().nullable(),
  user_id: z.string().uuid().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Folder = z.infer<typeof FolderSchema>

export const ExecutionLogSchema = z.object({
  id: z.string().uuid(),
  node_id: z.string().optional().nullable(),
  level: z.string(),
  message: z.string(),
  payload: z.record(z.string(), z.any()).optional().nullable(),
  timestamp: z.string(),
})

export type ExecutionLog = z.infer<typeof ExecutionLogSchema>

export const ExecutionSchema = z.object({
  id: z.string().uuid(),
  workflow_id: z.string().uuid(),
  status: z.string(),
  trigger_type: z.string(),
  input_data: z.record(z.string(), z.any()).optional().nullable(),
  output_data: z.record(z.string(), z.any()).optional().nullable(),
  started_at: z.string().optional().nullable(),
  finished_at: z.string().optional().nullable(),
  logs: z.array(ExecutionLogSchema),
})

export type Execution = z.infer<typeof ExecutionSchema>

export const CredentialSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  type: z.string(),
  meta: z.record(z.string(), z.any()).optional().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Credential = z.infer<typeof CredentialSchema>

export const OAuthUrlResponseSchema = z.object({
  url: z.string(),
  state: z.string(),
})

export type OAuthUrlResponse = z.infer<typeof OAuthUrlResponseSchema>

export const NodePropertySchema = z.object({
  name: z.string(),
  label: z.string(),
  type: z.string(),
  description: z.string().optional(),
  default: z.any().optional(),
  required: z.union([
    z.boolean(),
    z.object({
      field: z.string(),
      value: z.any(),
    }),
  ]).optional(),
  options: z.array(z.object({ label: z.string(), value: z.any() })).optional(),
  placeholder: z.string().optional(),
  condition: z.any().optional(),
  credentialType: z.union([z.string(), z.array(z.string())]).optional(),
  credentialTypeByField: z.object({
    field: z.string(),
    values: z.record(z.string(), z.string()),
  }).optional(),
  dependsOn: z.union([
    z.array(z.string()),
    z.object({
      all: z.array(z.string()).optional(),
      any: z.array(z.string()).optional(),
    }),
  ]).optional(),
  loadOptions: z.string().optional(),
  loadOptionsDependsOn: z.array(z.string()).optional(),
  mode: z.enum(['basic', 'advanced', 'both']).optional(),
  secret: z.boolean().optional(),
  visibility: z.enum(['user-or-llm', 'user-only', 'hidden']).optional(),
  canonicalId: z.string().optional(),
  group: z.string().optional(),
})

export const ApiNodeDefinitionSchema = z.object({
  type: z.string(),
  name: z.string(),
  category: z.enum(['trigger', 'action', 'logic', 'ai', 'browser', 'integration']),
  description: z.string(),
  icon: z.string(),
  color: z.string().optional(),
  properties: z.array(NodePropertySchema),
  inputs: z.number(),
  outputs: z.number(),
  outputs_schema: z.array(z.object({
    label: z.string(),
    type: z.string(),
  }).passthrough()).optional(),
  allow_error: z.boolean().optional(),
  credential_type: z.union([z.string(), z.array(z.string())]).nullable().optional(),
  tools: z.array(z.string()).nullable().optional(),
  operation_tool_map: z.record(z.string()).nullable().optional(),
})

export const ApiNodeDefinitionListSchema = z.array(ApiNodeDefinitionSchema)

export type ApiNodeDefinition = z.infer<typeof ApiNodeDefinitionSchema>

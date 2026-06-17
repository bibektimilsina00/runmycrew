import { z } from 'zod'
import type { Node, Edge } from 'reactflow'

// ── Workflow graph ────────────────────────────────────────────────────────────

export interface WorkflowGraph {
  nodes: Node[]
  edges: Edge[]
}

// ── Workflow (from backend) ───────────────────────────────────────────────────

export const WorkflowDetailSchema = z.object({
  id:             z.string().uuid(),
  name:           z.string(),
  description:    z.string().nullable().optional(),
  is_active:      z.boolean(),
  color:          z.string().nullable().optional(),
  graph:          z.any(),
  version_vector: z.number().default(0),
  created_at:     z.string(),
  updated_at:     z.string(),
})
export type WorkflowDetail = z.infer<typeof WorkflowDetailSchema>

// ── Save state ────────────────────────────────────────────────────────────────

export type SaveState = 'saved' | 'saving' | 'unsaved' | 'error'

// ── Node property types ───────────────────────────────────────────────────────

export type KnownNodePropertyType =
  | 'string' | 'number' | 'boolean' | 'json' | 'options' | 'multi-options'
  | 'credential' | 'key-value' | 'list' | 'messages' | 'schema' | 'file-list'
  | 'tool-selector' | 'skill-selector' | 'meta-resource' | 'wa-template'
  | 'code' | 'collection' | 'fixed-collection' | 'media' | 'gmail-query' | 'gdrive-folder'
  | 'google-file' | 'gsheet-tab' | 'gtasks-tasklist' | 'gpeople-group' | 'datetime'

export type NodePropertyType = KnownNodePropertyType | (string & {})

// Per-type renderer configuration
export interface TypeOptions {
  // string
  multiline?: boolean
  rows?: number
  password?: boolean
  maxLength?: number
  // number
  min?: number
  max?: number
  step?: number
  precision?: number
  // code
  language?: string
  // options / multi-options
  searchable?: boolean
  allowCustom?: boolean
  // collection
  multipleValues?: boolean
  addButtonText?: string
  sortable?: boolean
  [key: string]: unknown
}

export interface NodePropertyOption {
  label: string
  value: unknown
  description?: string
}

// Property visibility condition: a leaf (field equals value, or is one of value[])
// or a composite of nested conditions joined by `all` (every) / `any` (some).
export type PropertyCondition =
  | { field: string; value: unknown }
  | { all: PropertyCondition[] }
  | { any: PropertyCondition[] }

export interface NodeProperty {
  name: string
  label: string
  type: NodePropertyType
  description?: string
  default?: unknown
  required?: boolean | { field: string; value: unknown }
  options?: NodePropertyOption[]
  placeholder?: string
  // Conditional visibility — leaf { field, value } or composite { all | any: [...] }
  condition?: PropertyCondition
  // Per-type renderer config
  typeOptions?: TypeOptions
  // Sub-properties (for collection / fixed-collection)
  properties?: NodeProperty[]
  credentialType?: string | string[] | null
  credentialTypeByField?: { field: string; values: Record<string, string> }
  dependsOn?: string[] | { all?: string[]; any?: string[] }
  loadOptions?: string
  loadOptionsDependsOn?: string[]
  mode?: 'basic' | 'advanced' | 'both'
  secret?: boolean
  visibility?: 'user-or-llm' | 'user-only' | 'hidden'
  canonicalId?: string
  group?: string
}

export interface NodeDefinition {
  type: string
  name: string
  category: 'trigger' | 'action' | 'logic' | 'ai' | 'browser' | 'integration'
  description: string
  icon: string
  color?: string
  properties: NodeProperty[]
  inputs: number
  outputs: number
  outputsSchema?: { label: string; type: string }[]
  allowError?: boolean
  credentialType?: string
  tools?: string[]
  operationToolMap?: Record<string, string>
}

// ── Node definitions (from backend /nodes/) ───────────────────────────────────

const ConditionSchema: z.ZodType<PropertyCondition> = z.lazy(() =>
  z.union([
    z.object({ field: z.string(), value: z.any() }),
    z.object({ all: z.array(ConditionSchema) }),
    z.object({ any: z.array(ConditionSchema) }),
  ])
)

const NodePropertySchema: z.ZodType<NodeProperty> = z.lazy(() =>
  z.object({
    name:        z.string(),
    label:       z.string(),
    type:        z.string(),
    description: z.string().optional(),
    default:     z.any().optional(),
    required:    z.union([z.boolean(), z.object({ field: z.string(), value: z.any() })]).optional(),
    options:     z.array(z.object({ label: z.string(), value: z.any(), description: z.string().optional() })).optional(),
    placeholder: z.string().optional(),
    condition:   ConditionSchema.optional(),
    typeOptions: z.record(z.string(), z.any()).optional(),
    properties:  z.array(NodePropertySchema).optional(),
    credentialType: z.union([z.string(), z.array(z.string())]).nullable().optional(),
    credentialTypeByField: z.object({
      field: z.string(),
      values: z.record(z.string(), z.string()),
    }).optional(),
    dependsOn:   z.union([z.array(z.string()), z.object({ all: z.array(z.string()).optional(), any: z.array(z.string()).optional() })]).optional(),
    loadOptions: z.string().optional(),
    loadOptionsDependsOn: z.array(z.string()).optional(),
    mode:        z.enum(['basic', 'advanced', 'both']).optional(),
    secret:      z.boolean().optional(),
    visibility:  z.enum(['user-or-llm', 'user-only', 'hidden']).optional(),
    canonicalId: z.string().optional(),
    group:       z.string().optional(),
  }).passthrough()
)

export const ApiNodeDefinitionSchema = z.object({
  type:          z.string(),
  name:          z.string(),
  category:      z.enum(['trigger', 'action', 'logic', 'ai', 'browser', 'integration']),
  description:   z.string(),
  icon:          z.string(),
  color:         z.string().optional(),
  properties:    z.array(NodePropertySchema),
  inputs:        z.number(),
  outputs:       z.number(),
  outputs_schema: z.array(z.object({ label: z.string(), type: z.string() }).passthrough()).optional(),
  allow_error:   z.boolean().optional(),
  credential_type: z.union([z.string(), z.array(z.string())]).nullable().optional(),
})

export const ApiNodeDefinitionListSchema = z.array(ApiNodeDefinitionSchema)

export type ApiNodeDefinition = z.infer<typeof ApiNodeDefinitionSchema>

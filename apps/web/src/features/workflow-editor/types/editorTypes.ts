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
  // Distinguishes the full Automations editor from the focused Loop
  // Engineering editor. The palette narrows to AI-orchestration nodes
  // when kind === 'loop'. Optional + defaulted so pre-`kind` backends
  // (and any legacy rows) still parse as automations.
  kind:           z.enum(['automation', 'loop']).default('automation'),
  graph:          z.any(),
  version_vector: z.number().default(0),
  created_at:     z.string(),
  updated_at:     z.string(),
})
export type WorkflowDetail = z.infer<typeof WorkflowDetailSchema>

// ── Crew (from /crews backend) ────────────────────────────────────────────────
//
// Crews are the real backend model that superseded the old `kind=loop`
// workflow hack. The editor store is shared with workflows, so we parse the
// crew payload straight into the same `WorkflowDetail` shape the store reads.
// Crews have no `kind` / `version_vector` / `schema_version` — those store
// fields are defaulted here (`kind: 'automation'`, `version_vector: 0`) so the
// editor's version-vector + kind logic is inert for crews. The focused palette
// is instead forced via the editor store's `mode`, not `kind` (see
// useNodeLibrary + useWorkflowEditor). Crews additionally carry `position`.
export const CrewDetailSchema = z.object({
  id:             z.string().uuid(),
  name:           z.string(),
  description:    z.string().nullable().optional(),
  is_active:      z.boolean(),
  color:          z.string().nullable().optional(),
  position:       z.number().nullable().optional(),
  graph:          z.any(),
  created_at:     z.string(),
  updated_at:     z.string(),
  // Defaulted store-compat fields (crews don't send these).
  kind:           z.enum(['automation', 'loop']).default('automation'),
  version_vector: z.number().default(0),
})
export type CrewDetail = z.infer<typeof CrewDetailSchema>

// ── Save state ────────────────────────────────────────────────────────────────

export type SaveState = 'saved' | 'saving' | 'unsaved' | 'error'

// ── Node property types ───────────────────────────────────────────────────────

export type KnownNodePropertyType =
  | 'string' | 'number' | 'boolean' | 'json' | 'options' | 'multi-options'
  | 'credential' | 'key-value' | 'list' | 'messages' | 'schema' | 'file-list'
  | 'tool-selector' | 'skill-selector' | 'meta-resource' | 'wa-template'
  | 'code' | 'collection' | 'fixed-collection' | 'media' | 'gmail-query' | 'gdrive-folder'
  | 'google-file' | 'gsheet-tab' | 'gtasks-tasklist' | 'gpeople-group'
  | 'youtube-video' | 'youtube-playlist' | 'youtube-channel'
  | 'gchat-space' | 'ga4-property' | 'gsc-site' | 'gcs-bucket' | 'datetime'

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
  // When set on a `collection` with `multipleValues`, each new row's
  // named sub-field is pre-filled with `<prefix><N+1>` where N is the
  // highest current numeric suffix on that field. Lets generic
  // collections expose "auto-numbered name" UX without per-node code.
  autoIncrementField?: string
  autoIncrementPrefix?: string
  [key: string]: unknown
}

export interface NodePropertyOption {
  label: string
  value: unknown
  description?: string
}

// Property visibility condition.
//
// Leaf shape `{ field, value }` (optionally with `operator`) matches against
// one named field. `value: T` matches `=== T`; `value: T[]` matches
// "is one of". The optional `operator` flips that into negative matches:
//   - `eq`    → equals (default for scalar values)
//   - `notEq` → not equal
//   - `in`    → array includes (default for array values)
//   - `notIn` → array does NOT include
// Composite shapes join nested conditions via `all` (every) / `any` (some).
//
// Keep this in lockstep with `matchesCondition` in utils/nodeUtils.ts and
// the backend `condition` shape on `NodeMetadata.properties`.
export type ConditionOperator = 'eq' | 'notEq' | 'in' | 'notIn'

export type PropertyCondition =
  | { field: string; value: unknown; operator?: ConditionOperator }
  | { all: PropertyCondition[] }
  | { any: PropertyCondition[] }

/** Field-level remote picker descriptor.
 *
 * When set, the frontend renders `RemotePickerRenderer` instead of the
 * type's default renderer — hits `/credentials/{cred}/lookup/{provider}/
 * {resource}` on demand and shows a searchable dropdown. See the
 * backend `RemoteLookup` model in `rest_manifest.py` for the source of
 * truth. `${field}` in `params` values interpolates from sibling
 * property values on the same node.
 */
export interface RemoteLookupDescriptor {
  provider: string
  resource: string
  params: Record<string, string>
  depends_on: string[]
  allow_manual: boolean
}

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
  remote?: RemoteLookupDescriptor
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
  // When set, the inspector treats this node's outputs as DYNAMIC and
  // reads them from `node.data.properties[dynamicOutputsFrom]`, a
  // collection of `{name, type}` rows. Lets the Start node advertise
  // its user-defined inputs as the downstream `{{ $step.<field> }}`
  // completions without per-node-type checks in the autocomplete.
  dynamicOutputsFrom?: string
  allowError?: boolean
  credentialType?: string
  tools?: string[]
  operationToolMap?: Record<string, string>
  brand?: string | null
}

// ── Node definitions (from backend /nodes/) ───────────────────────────────────

const ConditionSchema: z.ZodType<PropertyCondition> = z.lazy(() =>
  z.union([
    z.object({
      field: z.string(),
      value: z.any(),
      operator: z.enum(['eq', 'notEq', 'in', 'notIn']).optional(),
    }),
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
    remote:      z.object({
      provider: z.string(),
      resource: z.string(),
      params: z.record(z.string(), z.string()).default({}),
      depends_on: z.array(z.string()).default([]),
      allow_manual: z.boolean().default(true),
    }).optional(),
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
  dynamic_outputs_from: z.string().nullable().optional(),
  allow_error:   z.boolean().optional(),
  credential_type: z.union([z.string(), z.array(z.string())]).nullable().optional(),
  brand:         z.string().nullable().optional(),
})

export const ApiNodeDefinitionListSchema = z.array(ApiNodeDefinitionSchema)

export type ApiNodeDefinition = z.infer<typeof ApiNodeDefinitionSchema>

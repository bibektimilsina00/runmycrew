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
  // Optional starter graph seeded on create. Matches the editor's persisted
  // graph shape ({ nodes, edges }); CrewCreate accepts it directly.
  graph?: { nodes: unknown[]; edges: unknown[] }
}

// ── Crew (from the dedicated /crews backend) ──────────────────────────────────
//
// The list UI still renders the `Loop` display shape (kind/trigger/status/…),
// but the real backend is now `/crews`, whose CrewOut payload is leaner — no
// kind/env/version. We parse CrewOut and map it into `Loop` (see crewToLoop)
// so the list page + row component stay unchanged.
export const CrewOutSchema = z.object({
  id:          z.string().uuid(),
  name:        z.string(),
  description: z.string().nullable().optional(),
  graph:       z.any(),
  is_active:   z.boolean(),
  position:    z.number().nullable().optional(),
  color:       z.string().nullable().optional(),
  max_cost_usd: z.number().optional().default(0),
  created_at:  z.string(),
  updated_at:  z.string(),
})
export type CrewOut = z.infer<typeof CrewOutSchema>

// Map a CrewOut into the `Loop` display shape the list expects. Crews have no
// execution stats or trigger metadata in the list payload, so those derive to
// sensible defaults; `status` follows is_active (active vs paused).
export function crewToLoop(c: CrewOut): Loop {
  return {
    id:              c.id,
    name:            c.name,
    description:     c.description ?? null,
    is_active:       c.is_active,
    color:          c.color ?? null,
    folder_id:      null,
    workspace_id:    '',
    user_id:         '',
    created_at:      c.created_at,
    updated_at:      c.updated_at,
    kind:            'agent',
    trigger:         '',
    status:          c.is_active ? 'active' : 'paused',
    execution_count: 0,
    last_run:        null,
    last_run_status: null,
  }
}

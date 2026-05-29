# Fuse Copilot — AI Workflow Generation & Editing (Implementation Plan)

Status: planning · Owner: TBD · Reference: Sim architecture writeup (`temp/AI_WORKFLOW_GENERATION.md`, gitignored)

## 1. Goal

A Copilot in the workflow editor that builds and edits workflows from natural language: the user describes intent in chat, the LLM calls an `edit_workflow(operations[])` tool, the engine applies operations to the graph with per-field validation and self-correcting feedback, and the result is shown as an **accept/reject diff** on the canvas. Also: a **"Fix with Copilot"** path that turns a node/run error into a repair request.

This is **brownfield** — the backend is ~80% built. The work is: wire the frontend, switch to a propose-diff model, harden the engine (validation + partial apply + structured feedback), add token streaming, fix layout/versioning, and add the fix flow.

## 2. Current state

### Backend (exists) — `apps/api/app/features/copilot/`
- `router.py` — `POST /copilot/{workflow_id}/chat` (SSE), `GET/PUT settings`, `GET/DELETE sessions`, `GET providers`. Mounted at `/api/v1/copilot`.
- `engine_core/engine.py` (606 lines) — agentic loop (max 10 iters), multi-provider callers (OpenAI/Anthropic/Google; Groq via openai_compatible), tools `edit_workflow` + `get_node_metadata`, **non-streaming** per-iteration LLM calls, SSE events, session save.
- `engine_core/operations.py` — `apply_operations(graph, ops, known_types)` → add/edit/delete node, add/delete edge; **all-or-nothing** (any error → nothing applied); always calls `auto_layout`.
- `engine_core/system_prompt.py` — node catalog (type/name/category + first 6 visible props) + simplified current graph + operations reference + rules.
- `engine_core/layout.py` — `auto_layout` (repositions **all** nodes).
- `service.py` — workflow auth, API-key resolution (per-user AES-encrypted credentials), per-workflow settings (stored in `workflow.env`), sessions, providers.
- `models.py` — `CopilotSession { id, workflow_id, user_id, title, messages[] }`.
- `schemas.py` — `CopilotChatRequest { messages[], graph?, provider, model?, credential_id?, session_id? }`, settings, sessions, providers.

### Frontend — **mock only**
- `hooks/useCopilotChat.ts` — local mock (`setTimeout` fake reply, slash commands). No network.
- `components/right-panel/panels/CopilotPanel.tsx` — UI shell bound to the mock.
- Zero references to `/copilot` anywhere in `apps/web`.

### Surrounding facts that constrain the design
- **Graph shape** (persisted `workflow.graph` JSONB, and ReactFlow store): `{ nodes: [{id, type, position, data:{label, properties}}], edges: [{id, source, target, sourceHandle?, targetHandle?, type}] }`. Node `type` is like `action.agent`, `trigger.manual`.
- **Store is the single source of truth** (`workflowEditorStore`) with `setNodes/setEdges`, `onNodesChange/onEdgesChange`, and **undo/redo** (`past/future`, `pushHistory`), clipboard, selection.
- **Autosave** = `PUT /workflows/{id}` with **`version_vector`** optimistic concurrency (see `useWorkflowEditor`, `cleanGraph`). On 409 the client resyncs version from the response and retries once.
- **Node definitions** = `GET /nodes/` returns full per-type schema (`NodeMetadata`): `properties[]` with `name, label, type, required, condition (leaf {field,value} | composite {all|any:[...]}), options, loadOptions, mode, visibility, credentialType, typeOptions, dependsOn`, plus `inputs/outputs/outputs_schema, allow_error, tools, operation_tool_map`. This is our `get_blocks_metadata` equivalent — already available.
- **Condition visibility is composite** (`shouldShowProperty` in `utils/nodeUtils.ts` handles leaf + all/any). Field requiredness must respect visibility.
- **Condition nodes** use dynamic per-row output handles (see `CLAUDE.md`: `ConditionNode` vs `CustomNode`). Edge `sourceHandle` matters for branching.
- Providers: `get_ai_providers()` (openai/anthropic/google/groq), tool-capable models required; credentials are per-user, AES-encrypted.

## 3. Decisions (locked)

| Topic | Decision |
|---|---|
| Apply model | **Propose diff → Accept/Reject** (not auto-apply) |
| Validation | **Robust per-field + partial apply + structured self-correction feedback** |
| Fix flow | **Included**, done properly (read/diagnostic tools, not a bolt-on) |
| Streaming | **Token-level** SSE streaming |
| Persistence | Copilot does **not** write the DB; **Accept** persists through the normal versioned `saveGraph` path (eliminates version races) |

## 4. Target architecture

Adapted from Sim, mapped to Fuse. Sim's four representations collapse for us because we already have one canonical graph.

- **A — Runtime/canvas state**: ReactFlow nodes/edges in `workflowEditorStore` (source of truth).
- **B — Persistence**: `workflow.graph` JSONB (same shape as A, cleaned). Already versioned.
- **D — AI-facing projection**: a compact JSON the LLM reads — nodes flattened to `{type, name, inputs, connections}` with edges embedded per source handle; positions/ui stripped. New (small) module. The LLM **never emits D** — it calls `edit_workflow(operations[])`.
- We do **not** need Sim's separate executor serialization (C) for copilot.

Flow:
```
User msg ── POST /copilot/{id}/chat {messages, graph(current canvas), provider, model, credential_id, session_id}
            │  (frontend sends the live canvas graph so copilot edits exactly what the user sees)
            ▼
run_copilot loop (in-memory working graph, seeded from request.graph)
   ├─ stream assistant tokens  ──► SSE text_delta
   ├─ tool: get_node_metadata  ──► SSE tool_call / tool_result
   ├─ tool: get_recent_run/logs (fix flow) ──► read-only
   ├─ tool: edit_workflow(ops) ──► validate + partial-apply to working graph
   │        ──► SSE tool_result {success, applied, inputValidationErrors, skippedItems, lint}
   │        (LLM self-corrects next iteration using these)
   └─ on finish ──► SSE workflow_proposed {proposedGraph}   (NO DB write)
                    SSE session_saved, done
            ▼
Frontend: diff(currentGraph, proposedGraph) ──► colored overlay + Accept/Reject
   Accept ─► store.setNodes/setEdges(proposed) ─► existing autosave PUT (version_vector)
   Reject ─► discard, keep baseline
```

## 5. Milestones

Ship in this order; each is independently testable.

- **M1 — Token streaming + SSE contract** (backend). Rewrite the three provider callers to stream; define the canonical SSE event set (§7). Tool calls assembled from streamed deltas.
- **M2 — Node-schema discovery + compression + validation** (backend). Scale node context to 200–1000+ types via two-tier lazy discovery + a compressed projection that is **shared by the prompt index, the `get_node_metadata` tool, and the validator** (§7b, §9).
- **M3 — Propose-diff model** (backend + frontend). Engine stops writing the DB; emits `workflow_proposed`. Frontend diff store + overlay + Accept/Reject (§10).
- **M4 — Layout & version correctness** (backend). `auto_layout` only positions new/unpositioned nodes; existing positions preserved. Accept persists via versioned path (§11).
- **M5 — Frontend chat wiring** (frontend). Replace the mock `useCopilotChat` with a real SSE client (fetch + ReadableStream + AbortController), provider/model picker, sessions list, cancel/regenerate.
- **M6 — Fix with Copilot** (backend + frontend). Read/diagnostic tools (`get_recent_run`, `get_node_error`/logs) + prefilled-message entry points from node context menu and run errors (§12).

> M1/M2/M4 can land before the frontend (M5) using the existing panel against a curl/test harness. M3 needs both.

## 6. SSE event contract (§7 detail)

All events are `data: {json}\n\n`. `type` is the discriminant.

| `type` | payload | meaning |
|---|---|---|
| `text_delta` | `{ content }` | streamed assistant token chunk |
| `tool_call` | `{ id, name, args? }` | model invoked a tool |
| `tool_result` | `{ id, name, success, summary, inputValidationErrors?, skippedItems?, lint? }` | tool outcome (feedback also fed back to the model) |
| `workflow_proposed` | `{ proposedGraph }` | final proposed graph after the loop (frontend diffs vs current) |
| `session_saved` | `{ session_id, title }` | persisted chat session |
| `error` | `{ message }` | fatal stream error |
| `done` | `{}` | stream complete |

Notes: drop the current `workflow_updated` auto-apply event. Frontend renders `text_delta` as a typewriter, shows tool chips from `tool_call`/`tool_result`, and triggers the diff on `workflow_proposed`.

## 7. AI-facing projection D (§8 detail)

New module `engine_core/projection.py`. `to_copilot_graph(graph, node_metadata)`:
- For each node: `{ type, name, inputs: <data.properties minus null/empty>, connections: { <sourceHandle or "source">: targetId | [targetId...] } }`, keyed by node id.
- Strip `position`, ui flags. Keep enough for the LLM to reason about wiring.
- Used in the system prompt instead of today's "simplified graph" (richer; includes inputs + handles). Hand to the model as `JSON.stringify(projection, null, 2)`.

`edit_workflow` keeps the operations API (already implemented). Document param shapes precisely in the tool description — that *is* most of the prompt. Add `connections` support to `add_node`/`edit_node` params (currently edges are separate `add_edge` ops; keep both, but allowing inline `connections` lets the model build in fewer ops). Handle naming: teach semantic handles for condition/branch nodes.

## 7b. Scaling node-schema context (200–1000+ node types)

**Problem:** the registry will reach hundreds-to-1000+ node types (every integration × many operations). You cannot put every type's full field schema in the prompt. Today `system_prompt.py` dumps **every** type **+ 6 props each**, and `get_node_metadata` returns the **raw full** `NodeMetadata` for one type — neither scales.

**Solution (from Sim §7.5): two-tier lazy discovery + compressed projection. Prompt size scales with node-types-per-task (~3–10), not node-types-that-exist.**

### Tier 1 — bounded index in the prompt
Put only a small, bounded index in the system prompt — never the whole registry:
- the **category list**;
- **all trigger nodes** (the legal workflow starters — few);
- a **curated "core" set** (~20–40 common nodes: agent, http_request, condition, loop, code, response, …) as `{type, name, one-line desc}` grouped by category.

That's the entire "what exists" budget and it stays ~constant as the registry grows.

### Tier 2 — on-demand discovery tools
- **`search_node_types(query)`** — long-tail discovery for everything not in the core index. Substring/keyword match over `{type, name, description, category}` now; swap to embedding/pgvector RAG later behind the same interface. Returns `[{type, name, description}]`.
- **`get_trigger_nodes()`** — cheap menu of starter node types.
- **`get_node_metadata(types[])`** — accept an **array** (today: single); return the **compressed projection** below for only the requested types.

Planner loop: read index → `search_node_types` if the needed type isn't in core → `get_node_metadata([chosen types])` → emit `edit_workflow` operations.

### The compressed projection (NOT raw `NodeMetadata`)
A pure function `project_node(metadata) -> CompactNodeSchema`, **shared** by the Tier-1 index builder, the `get_node_metadata` tool, and the validator (§9). Per type:
1. **Map property `type` → simple JSON type**: `string|number|boolean|json|options→string(enum)|key-value→object|credential|file-list→array|...`.
2. **Split `required` vs `optional`** flat arrays of `{name, type, description, options?, default?, example?}`. Required honors **visibility** (a field required only when its `condition` is satisfied — reuse the composite `all/any` semantics).
3. **Bucket operation-gated fields by operation.** Fields whose `condition.field == "operation"` (Slack/Discord/Notion/HTTP/etc.) are pulled out of the common set and grouped: `operations: { send_message: {inputs:{required,optional}, outputs}, ... }`. Common (always-visible) fields stay top-level. Stops the model setting wrong-operation fields.
4. **`loadOptions` fields → mark dynamic** (`{type, dynamic:true, note:"options fetched at runtime"}`); do **not** enumerate (network/credential-dependent — same as Sim skipping async `fetchOptions`). Static `options` arrays → include enum values.
5. **Strip** `visibility:'hidden'`, secret values, advanced-UI-only noise, internal `typeOptions` the model doesn't need.
6. **Attach** `outputs`/`outputs_schema` (for wiring references), `credentialType`/auth requirement, `tools`/`operationToolMap` if relevant, and a short generated `example` per key.

### Permission / allow-list filtering
All three discovery tools filter server-side by the user's allowed integrations / available credentials. A node the user can't use is dropped from index + search + metadata — the model can't even learn its schema. Enforced at fetch, not in the prompt.

### Current-graph budget
The embedded current graph also grows with the user's workflow. Keep the projection compact (id, type, name, connections) and, for very large graphs, summarize/truncate distant nodes — scales with the user's own workflow, not the registry.

### Replication checklist (Fuse-specific)
- [ ] `project_node()` compressed projection (shared module).
- [ ] Tier-1 index builder: categories + triggers + curated core (config-driven `CORE_NODE_TYPES`).
- [ ] `search_node_types`, `get_trigger_nodes` tools; `get_node_metadata` → array + projection.
- [ ] permission/credential allow-list filter applied to all three.
- [ ] validator consumes the same projection so prompt and validation never drift.

## 8. Validation & feedback contract (§9 detail)

New `engine_core/validation.py`:
- `validate_node_inputs(node_type, properties, metadata) -> (clean_props, errors[])`:
  - resolve the type's `properties[]` schema;
  - for each provided input: check the field exists; coerce/validate by `type` (number, boolean, options enum membership, json shape, credential id format);
  - **required** enforced only when the field is *visible* given current values (reuse the same composite-condition logic as the frontend `shouldShowProperty` — port to Python or share contract);
  - unknown fields → warning (dropped), not fatal.
- `apply_operations` becomes **partial**: apply every valid operation; collect `ValidationError { node_id, node_type, field, value, error }` and `SkippedItem { op, reason }` (unknown type, missing node, invalid edge endpoint/handle, duplicate). Return `(updated_graph, applied[], inputErrors[], skipped[], lint)`.
- `lint(graph)`: orphan nodes (no incoming edge and not a trigger), dangling edges, condition nodes with unconnected branches.
- Engine surfaces these in `tool_result.summary` + structured fields so the LLM fixes itself next iteration. **Save valid parts even on partial failure.**

## 9. Diff store & Accept/Reject (§10 detail)

Frontend `stores/copilotDiffStore.ts` (or extend editor store):
- `proposedGraph`, `baselineGraph`, `isShowingDiff`.
- `setProposal(proposed)` — snapshot baseline = current store graph; compute diff:
  - node markers: `new` | `edited` | `deleted`; field-level `changed` set per edited node;
  - edge markers via key `${source}-${sourceHandle||'source'}-${target}-${targetHandle||'target'}`.
- Render: overlay proposed nodes/edges with colored borders/badges (green new, amber edited, red deleted ghost). Deleted nodes shown as ghosts until accept.
- `accept()` — `setNodes/setEdges(proposed)`, clear diff, let autosave persist (versioned). Push one `pushHistory()` first so Accept is undoable.
- `reject()` — clear proposal, keep baseline. No persist.
- While a diff is active, block new copilot sends until resolved (or auto-reject on new send).

## 10. Layout & version coordination (§11 detail)

- `auto_layout`: accept the existing graph; **only assign positions to nodes lacking one or newly added**; keep user-positioned nodes fixed. Place a new node near its connected source (offset right/below); grid-fallback for orphans.
- Versioning: because Accept goes through the existing `saveGraph` (which sends `version_vector`), copilot never races the autosave. Remove `repo.update` from the engine entirely. If we later want server-side persistence during the loop, it must bump `version_vector` and the frontend must resync — avoided for now.

## 11. Fix with Copilot (§12 detail)

- **Read/diagnostic tools** (route through the loop, read-only):
  - `get_recent_run(workflow_id)` → last run status + per-node results/errors (from the `runs` feature).
  - `get_node_error(node_id)` → the error string + the node's resolved inputs.
- **Entry points** (frontend), both producing the same seed message and dispatching to the copilot panel:
  - Node context menu (already built) → "Fix with Copilot" on a node that errored in the last run.
  - Run/log error row → "Fix with Copilot".
  - Seed: `"{error}\n\nError in {nodeName}.\n\nPlease fix this."` dispatched via a window event the panel listens for (`copilot-send-message`).
- The agent inspects via the read tools, then calls `edit_workflow` to repair → normal diff/accept.

## 12. Frontend chat client (M5 detail)

Rewrite `useCopilotChat.ts`:
- Real send: `fetch('/api/v1/copilot/{id}/chat', { method:'POST', body, signal })`, read `response.body.getReader()`, parse SSE lines, dispatch by `type`.
- State: `messages[]` (user/assistant w/ streaming text + tool chips), `streaming`, `proposalActive`, `error`.
- Send the **current canvas graph** in the request so copilot edits what the user sees.
- `AbortController` for **cancel**; **regenerate** re-sends last user turn.
- Provider/model/credential from `GET /copilot/providers` + per-workflow settings (`GET/PUT settings`); selector in the panel.
- Sessions: list/load/delete via existing endpoints; "New chat".
- On `workflow_proposed` → `copilotDiffStore.setProposal`.
- Keep slash commands (`/fix`, `/explain`, …) as message prefills.

## 13. Testing

- Backend unit: `validate_node_inputs` (required-when-visible, options enum, type coercion); `apply_operations` partial apply + structured errors; `auto_layout` preserves existing positions; projection D shape.
- Backend integration: mock LLM returning canned tool calls → assert SSE event sequence + proposed graph (no DB write); session save.
- Provider streaming parsers: unit tests per provider with recorded SSE fixtures.
- Frontend: SSE parser; diff computation (new/edited/deleted/edge keys); accept persists (version path) and is undoable; reject restores.
- E2E (manual): "build a workflow that fetches a URL and summarizes it" → diff → accept → autosave; then "add a Slack notification on success" → edit diff; then break a node, "Fix with Copilot".

## 14. Risks / notes

- **Token streaming is provider-specific** (OpenAI `stream:true` SSE deltas incl. tool-call argument deltas; Anthropic `messages` SSE `content_block_delta` incl. `input_json_delta`; Google `streamGenerateContent`). Assemble tool calls from deltas carefully. Most effort lives here.
- **Required-when-visible** validation must match the frontend's composite condition semantics exactly — share a contract / port `shouldShowProperty` logic to Python and unit-test parity.
- **Diff while editing**: lock the canvas (or the diffed nodes) while a proposal is pending to avoid conflicting manual edits.
- **Condition/branch handles**: the projection + tool docs must teach semantic source handles or the model will mis-wire branches.
- Keep the **operations API stable** — it is the contract; the prompt is secondary.

## 15. File-by-file checklist

Backend (`apps/api/app/features/copilot/`):
- [ ] `engine_core/engine.py` — token-streaming callers (3 providers) + delta→tool-call assembly; emit new SSE contract; **remove DB write**; emit `workflow_proposed`; wire read tools.
- [ ] `engine_core/node_schema.py` — **new**: `project_node()` compressed projection + Tier-1 index builder (categories + triggers + curated `CORE_NODE_TYPES`); shared by prompt, tools, validator (§7b).
- [ ] discovery tools — **new**: `search_node_types`, `get_trigger_nodes`; `get_node_metadata` → array input + projection; permission/credential allow-list filter on all three.
- [ ] `engine_core/validation.py` — **new**: per-field validation (consumes `project_node`) + lint.
- [ ] `engine_core/operations.py` — partial apply + structured errors; inline `connections` support.
- [ ] `engine_core/projection.py` — **new**: AI-facing graph D (current-graph compaction/truncation).
- [ ] `engine_core/system_prompt.py` — bounded Tier-1 index (not full registry); use projection D; richer tool/handle docs; condition-branch guidance.
- [ ] `engine_core/layout.py` — only position new/unpositioned nodes.
- [ ] read-tools (run/logs) — new tool specs + handlers; depends on `features/runs`.
- [ ] tests.

Frontend (`apps/web/src/features/workflow-editor/`):
- [ ] `hooks/useCopilotChat.ts` — real SSE client (rewrite).
- [ ] `stores/copilotDiffStore.ts` — **new** diff/accept/reject.
- [ ] `components/right-panel/panels/CopilotPanel.tsx` — streaming text, tool chips, provider/model picker, sessions, cancel/regenerate, diff banner.
- [ ] canvas — render diff markers (new/edited/deleted ghosts); lock during proposal.
- [ ] context menu — "Fix with Copilot" entry; window-event bridge to the panel.
- [ ] `services/copilotAPI.ts` — **new**: providers/settings/sessions calls.
```
```

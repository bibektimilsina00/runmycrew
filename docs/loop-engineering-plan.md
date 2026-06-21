# Loop Engineering — complete design + implementation guide

> **Status:** Draft for discussion.
> **Owner:** Bibek
> **Last updated:** 2026-06-21
> **Companion PR:** docs-only — no code lands here. Reviewers should
> comment inline before any implementation PR is opened.

---

## Table of contents

- [1. Introduction](#1-introduction)
- [2. Vision & problem statement](#2-vision--problem-statement)
- [3. Use cases](#3-use-cases)
- [4. Glossary](#4-glossary)
- [5. Current state of the codebase](#5-current-state-of-the-codebase)
- [6. Gap analysis](#6-gap-analysis)
- [7. Architecture overview](#7-architecture-overview)
- [8. Component specifications](#8-component-specifications)
- [9. Data model](#9-data-model)
- [10. API surfaces](#10-api-surfaces)
- [11. Frontend UX](#11-frontend-ux)
- [12. Templates](#12-templates)
- [13. Implementation phases](#13-implementation-phases)
- [14. Testing strategy](#14-testing-strategy)
- [15. Migration plan](#15-migration-plan)
- [16. Operational concerns](#16-operational-concerns)
- [17. Performance budget](#17-performance-budget)
- [18. Risks & mitigations](#18-risks--mitigations)
- [19. Open questions](#19-open-questions)
- [20. Non-goals](#20-non-goals)
- [21. FAQ](#21-faq)
- [22. Code sketches](#22-code-sketches)

---

## 1. Introduction

### 1.1 What is "loop engineering"?

**Loop engineering** is the practice of running an AI agent inside an
automated, scheduled loop so that it can autonomously own a recurring
task — checking inputs, taking action, retrying on failure, escalating
when stuck — without a human prompting it each time.

A loop has four parts:

1. **A trigger** — usually a clock (every 5 min, every hour), but can
   also be a queue / webhook.
2. **A goal** — a short instruction in plain English ("triage new bug
   reports").
3. **A toolbox** — the set of integrations the agent is allowed to use
   (read Linear, write Slack, comment on GitHub, etc).
4. **A stop condition** — when does this loop consider itself done.

Once these four things exist as a single workflow, the agent runs
itself.

### 1.2 Why does it matter for RunMyCrew?

Today most automation platforms (Zapier, Make, n8n) ship **reactive
workflows**: input → fixed pipeline → output. They cannot reason about
intermediate state. The user is the loop.

LLMs changed that. A single agent can now:
- read an inbox,
- decide what's spam,
- draft a reply,
- check whether the reply makes sense,
- send it,
- log what was done.

But this only matters if the loop runs **without a human at the wheel**.
Loop engineering is the platform-side work to make that safe at 24/7
scale: budgets, concurrency, traces, failure handling.

RunMyCrew is uniquely positioned to ship this because we already have:
- a workflow engine,
- 80+ integration nodes (potential agent tools),
- credential management,
- AI agent + memory primitives.

What we're missing is the **loop hardening** — the operational scaffold
around the agent.

---

## 2. Vision & problem statement

### 2.1 Vision

> A RunMyCrew user can describe a recurring operations task in one
> sentence, drag in the apps the agent should use, set a schedule,
> and walk away. The agent owns the task end-to-end. The user reads
> a daily digest of what was handled, what was escalated, and what
> cost.

### 2.2 Problem statement (current pain)

Without loop engineering, a user wanting "auto-triage Linear bugs"
today has to:

1. Build a static workflow: Cron → fetch issues → for each issue → call
   LLM → parse output → if `label == X` then `set_label` → repeat.
2. Hard-code every branch the LLM might pick.
3. Hand-write retry logic when the LLM hallucinates a bad label.
4. Hand-write escalation when retries exhaust.
5. Watch the workflow runs to confirm it's behaving.

This is doable but **fragile + verbose**. Every new sub-action requires
adding nodes to the graph.

A loop-engineered workflow collapses steps 1–5 into:

```
Cron(every 30m) → AgentLoop(goal="triage Linear bugs", tools=[linear.*, slack.escalate])
```

The agent decides what to call and in what order. Adding a new action
type means dropping a new tool into the `tools` array — no rewiring.

### 2.3 Success criteria

A v1 of loop engineering is successful if:

1. A user can build the "Linear triage" loop in <5 minutes.
2. The loop runs for 7 days unattended without crashing the worker,
   busting budget, or corrupting state.
3. When the loop screws up, the user can read the trace and understand
   exactly which step went wrong.
4. The same user can rejig the loop by adding/removing a tool without
   editing graph topology.
5. Operational cost stays predictable — known max tokens per fire.

---

## 3. Use cases

Real things real users want to automate that loop engineering
unlocks.

### 3.1 Triage Linear bug queue

- **Trigger:** every 30 min.
- **Goal:** "For each issue in the `Bug` queue with no label, pick a
  label (`frontend`, `backend`, `infra`, `unknown`) and a priority
  (`P0`, `P1`, `P2`) based on the title + description. If `P0`, also
  post to `#oncall` Slack channel."
- **Tools:** `linear.list_issues`, `linear.update_issue`,
  `slack.post_message`.
- **Stop condition:** all bugs in queue have a label.

### 3.2 Dependabot auto-merger

- **Trigger:** webhook on `pull_request.opened`.
- **Goal:** "If PR author is Dependabot and bump is patch or minor and
  CI is green, merge it. Otherwise post the PR to `#dependencies`
  channel for human review."
- **Tools:** `github.get_pr`, `github.get_pr_checks`, `github.merge_pr`,
  `slack.post_message`.
- **Stop condition:** the PR is either merged or escalated.

### 3.3 Sentry → GitHub issue

- **Trigger:** every 15 min.
- **Goal:** "For each new Sentry issue since last run, check if a
  GitHub issue already references the fingerprint. If not, create a
  GitHub issue with the stack trace + frequency."
- **Tools:** `sentry.list_issues`, `github.search_issues`,
  `github.create_issue`, `memory.set('last_seen_sentry_id')`.
- **Stop condition:** all new Sentry issues are either ignored or
  filed.

### 3.4 Standup digest

- **Trigger:** every weekday 9:00 AM.
- **Goal:** "Summarize yesterday's GitHub commits + closed Linear
  issues + open PRs. Post a digest to `#standup`."
- **Tools:** `github.list_commits`, `linear.list_issues`,
  `github.list_prs`, `slack.post_message`.
- **Stop condition:** digest posted.

### 3.5 Stale PR reminder

- **Trigger:** every Mon/Wed/Fri 10:00 AM.
- **Goal:** "Find PRs open >7 days with no activity. For each, DM the
  author asking for status. If author is offline (vacation in HR), DM
  the PR's first reviewer instead."
- **Tools:** `github.list_prs`, `slack.dm_user`, `hr.get_user_status`.
- **Stop condition:** all stale PRs have been pinged.

### 3.6 Customer support triage

- **Trigger:** webhook on new ticket.
- **Goal:** "Classify ticket urgency. If urgent + paying customer,
  page on-call via PagerDuty. Else, route to the right team queue
  using the team-to-keyword map."
- **Tools:** `intercom.get_ticket`, `intercom.tag`, `pagerduty.page`,
  `crm.get_customer_tier`.
- **Stop condition:** ticket is routed or paged.

### 3.7 Patterns across all the above

| Pattern | Loop engineering response |
|---------|---------------------------|
| "For each X" iteration | LLM decides how many iterations are needed inside the loop, no explicit foreach |
| Branchy logic | LLM picks the branch; no if/else nodes needed |
| Retry on flaky API | Existing `ToolRetryConfig` handles tool-level; loop handles workflow-level |
| Escalation | One declarative `failure_policy: escalate` field; routes to a configured handler |
| Memory across runs | Existing memory node holds "last_seen_X" pointers |

---

## 4. Glossary

| Term | Meaning |
|------|---------|
| **Agent** | A single LLM call with a system prompt + optional tools. |
| **Agent Loop** | A series of agent calls that share message history, until a stop condition fires. |
| **ReAct** | The "Reason–Act–Observe" agent loop pattern: the LLM thinks, picks a tool, sees the result, thinks again. |
| **Tool** | A function the agent can call. In RunMyCrew, every node is a potential tool. |
| **Tool call** | A single invocation of a tool from inside the loop. |
| **Trace** | The ordered list of thought/tool/observation triples produced by a loop run. |
| **Goal** | The plain-English task the loop is trying to accomplish. |
| **Stop condition** | Either an iteration cap, a time cap, a token cap, a cost cap, or a `success_when` expression evaluating to truthy on the loop's result. |
| **Concurrency policy** | What happens when the loop is triggered while a previous run is still in flight. |
| **Cron drift** | The clock difference between when a cron should have fired and when it actually fired (because the worker was busy). |
| **Skill** | A reusable prompt fragment loaded into the loop's system prompt (existing concept in `agent.py`). |
| **MCP** | Model Context Protocol — an external tool-server protocol the loop can speak. |
| **Memory key** | A stable string that identifies persistent state across loop runs. |
| **Workspace** | RunMyCrew's tenancy boundary; loops scoped to one workspace. |

---

## 5. Current state of the codebase

What we already have. (File paths are relative to repo root.)

### 5.1 Triggers

| Capability | File |
|------------|------|
| Cron trigger | `apps/api/app/node_system/nodes/common/cron/cron_node.py` |
| Webhook trigger | `apps/api/app/node_system/nodes/http/webhook/webhook.py` |
| Manual trigger | `apps/api/app/node_system/nodes/common/trigger/` |

### 5.2 AI runtime

| Capability | File |
|------------|------|
| LLM call (single shot) | `apps/api/app/node_system/nodes/ai/llm/llm.py` |
| **Agent node with tools + max_iter** | `apps/api/app/node_system/nodes/ai/agent/agent.py` |
| Memory node | `apps/api/app/node_system/nodes/ai/memory/memory_node.py` |
| Memory providers (redis-backed) | `apps/api/app/node_system/nodes/ai/agent/memory/providers.py` |
| Skills loader | referenced via `AgentProperties.skills` |
| MCP server config | `AgentProperties.mcpServers` |
| Evaluator (binary judge) | `apps/api/app/node_system/nodes/ai/evaluator/evaluator.py` |
| Thinking node | `apps/api/app/node_system/nodes/ai/thinking/` |

### 5.3 Control flow

| Capability | File |
|------------|------|
| `for_loop` | `apps/api/app/node_system/nodes/logic/for_loop/` |
| `while_loop` | `apps/api/app/node_system/nodes/logic/while_loop/while_loop.py` |
| `do_while` | `apps/api/app/node_system/nodes/logic/do_while/` |
| `foreach` | `apps/api/app/node_system/nodes/logic/foreach/` |
| `sub_workflow` | `apps/api/app/node_system/nodes/logic/sub_workflow/sub_workflow_node.py` |
| `human_input` (HITL pause) | `apps/api/app/node_system/nodes/logic/human_input/` |
| `code` (Python sandbox) | `apps/api/app/node_system/nodes/logic/code/sandbox.py` |

### 5.4 Engine

| Capability | File |
|------------|------|
| Workflow runner | `apps/api/app/execution_engine/engine/workflow_runner.py` |
| Per-runner async lock | `workflow_runner.py` line ~71 (`self._lock`) |
| Scheduler / cron | `apps/api/app/execution_engine/scheduler/cron.py` |
| Run history | `apps/api/app/features/runs/` |

### 5.5 What's missing

- Cross-run / workflow-level concurrency mutex (Redis-backed).
- Per-loop time + cost + token budgets enforced as hard cutoffs.
- Structured trace persisted to the run record (today it's logs).
- Frontend trace viewer (chat-style timeline) in the logs panel.
- `success_when` declarative stop expression.
- Failure-policy with a built-in escalation handler.
- Cron-drift policy field (catchup / skip / latest-only).
- Workspace-level loop dashboard (which loops are running, P&L, last
  failure).

---

## 6. Gap analysis

Each gap, sized + priority-tagged.

| # | Gap | Priority | Effort | Phase |
|---|-----|----------|--------|-------|
| G1 | Cross-run concurrency mutex (Redis) | P0 | 1 day | 2 |
| G2 | `success_when` JSONata expression evaluation in agent | P0 | 0.5 day | 1 |
| G3 | Hard token + time + cost budgets on agent | P0 | 1 day | 1 |
| G4 | Structured `trace[]` output schema + persistence | P0 | 1 day | 1 |
| G5 | Failure-policy field (`escalate` / `retry` / `silent`) | P0 | 0.5 day | 1 |
| G6 | Tool-from-node auto-schema (polish existing partial impl) | P1 | 1 day | 4 |
| G7 | Per-tool permission toggle in inspector | P1 | 0.5 day | 4 |
| G8 | Frontend trace viewer (chat timeline) in logs panel | P1 | 2 days | 3 |
| G9 | Cron drift policy field | P2 | 1 day | 5 |
| G10 | Workspace-level loop dashboard | P2 | 2 days | post-v1 |
| G11 | Bundled escalation handler (Slack/email) | P2 | 0.5 day | 6 |
| G12 | Built-in MCP servers (filesystem, web) | P3 | open | post-v1 |
| G13 | Multi-agent debate / hand-off | P3 | open | post-v1 |

**P0 items are the v1 cut.**

---

## 7. Architecture overview

### 7.1 High-level data flow

```
                                  ┌──────────────┐
                                  │   Trigger    │  (cron / webhook / manual)
                                  └──────┬───────┘
                                         │ fires
                                         ▼
                          ┌────────────────────────────────┐
                          │   Concurrency mutex (Redis)    │
                          │   ───────────────────────────  │
                          │   SET NX  key=workflow:{id}    │
                          │   policy=skip|queue|replace    │
                          └──────┬─────────────────────────┘
                                 │ acquired
                                 ▼
                  ┌────────────────────────────────────────┐
                  │           AgentLoop node               │
                  │           ───────────────              │
                  │                                        │
                  │   ┌──── Tool registry (built from      │
                  │   │     each tool node's NodeMetadata) │
                  │   │                                    │
                  │   ▼                                    │
                  │  ┌─── ReAct loop ──────────────────┐   │
                  │  │                                  │  │
                  │  │   Budget Enforcer  ◄────────┐   │  │
                  │  │   ─────────────────         │   │  │
                  │  │   max_iter / max_seconds /  │   │  │
                  │  │   max_tokens / max_cost     │   │  │
                  │  │                             │   │  │
                  │  │   thought ──► tool_call ─►  │   │  │
                  │  │      ▲          │           │   │  │
                  │  │      │          ▼           │   │  │
                  │  │   observation ◄┘            │   │  │
                  │  │      │                      │   │  │
                  │  │      ▼                      │   │  │
                  │  │   success_when match? ──────┘   │  │
                  │  │      │                          │  │
                  │  │      ▼ yes                      │  │
                  │  │   exit success                  │  │
                  │  └─────────────────────────────────┘  │
                  │                                       │
                  │   Trace[] streamed to runner via SSE  │
                  │   Memory: durable cross-run state     │
                  └────────────────┬──────────────────────┘
                                   │ status
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
            success         budget_exhausted        failed
                ▼                  ▼                  ▼
          exit ok            exit warn           failure_policy
                                                       │
                                                       ▼
                                         escalate / retry / silent
                                                       │
                                                       ▼
                                            Trace + audit persisted
                                            Mutex released
```

### 7.2 Component boundaries

| Layer | Responsibility |
|-------|---------------|
| **Trigger** | Decide when the loop fires |
| **Concurrency mutex** | Decide whether THIS fire is allowed to run |
| **Loop runtime** | Execute the ReAct cycle; enforce budgets; collect trace |
| **Tool registry** | Map tool name → node executor; build JSON schema |
| **Budget enforcer** | Hard-stop the loop when any budget exhausted |
| **Trace persistence** | Stream + store trace steps to run record |
| **Memory** | Hand the loop a per-`memory_key` k/v store |
| **Failure handler** | Route the final state to the configured policy |
| **Frontend** | Render trace + per-tool result + cost in the logs panel |

Each layer is independently swappable. The mutex can be swapped from
Redis to Postgres advisory locks without touching the runtime.

### 7.3 Sequence: one cron fire

```
Cron fires
  │
  ├─► Runner.acquire_concurrency_lock(workflow_id, policy)
  │     ├─ skipped: log "skipped_concurrent" → exit
  │     ├─ queued:  wait
  │     └─ ok:      proceed
  │
  ├─► Runner.start_run(workflow_id)
  │     └─ creates RunRecord(state="running")
  │
  ├─► Resolve AgentLoop node
  │     ├─ build tool registry from `tools` input
  │     └─ inject memory provider for `memory_key`
  │
  ├─► ReAct loop
  │     ├─ iteration 1: llm.complete(messages) → tool_call
  │     │   ├─ budget check (iter, time, tokens, cost)
  │     │   ├─ tool_registry[name](args)
  │     │   ├─ append observation
  │     │   └─ emit trace step over SSE
  │     ├─ iteration N: → final response
  │     │   └─ if success_when matches → break
  │     └─ exit
  │
  ├─► Persist trace + usage to RunRecord
  ├─► Runner.release_concurrency_lock(workflow_id)
  └─► Audit: { status, iterations, cost_usd, trace_id }
```

---

## 8. Component specifications

Detailed contract for each new + extended component.

### 8.1 `ai.agent_loop` node

Replaces the existing `ai.agent` as the recommended entry point for
autonomous loops. The existing `ai.agent` stays for single-pass use.

#### 8.1.1 Properties

```jsonc
{
  // Required
  "goal":          "string",      // plain-English task; becomes part of system prompt
  "llm":           "credential",  // OpenAI / Anthropic / Gemini / Groq / ...

  // Tools
  "tools":         "node-refs[]", // references to other nodes in this workflow
  "tools_policy":  "auto",        // future: "manual" (LLM proposes, human approves)

  // Loop semantics
  "max_iterations":   10,         // hard cap on ReAct cycles
  "max_seconds":      600,        // hard cap on wall-clock
  "max_input_tokens": 100000,     // hard cap on input tokens summed across iterations
  "max_cost_usd":     0.50,       // hard cap on LLM spend

  // Stop conditions
  "success_when":  "$.action_taken == true",  // JSONata; matched against final result
  "min_iterations": 0,            // safety: don't exit before this many iterations

  // Failure handling
  "failure_policy": "escalate",   // 'escalate' | 'retry' | 'silent'
  "retry_count":    1,            // if failure_policy='retry'

  // State
  "memory_key":    "linear-triage",  // namespace for cross-run memory
  "skills":        ["triage-tone"],  // existing skills system

  // Streaming
  "stream_trace":  true,          // SSE trace steps to the frontend

  // Identity
  "identity":      "RunMyCrew Triage Bot",  // shows up in tool calls
}
```

#### 8.1.2 Outputs

```jsonc
{
  "status":     "success | budget_exhausted | failed | no_op | skipped_concurrent",
  "iterations": 4,
  "result":     { /* whatever the agent returned */ },
  "trace": [
    {
      "step":          0,
      "thought":       "I should list the open bugs first",
      "tool_call":     { "name": "linear.list_issues", "args": { "queue": "Bug" } },
      "tool_result":   { "items": [ /* ... */ ] },
      "tool_duration_ms": 423,
      "tokens_in":     1820,
      "tokens_out":    87,
      "cost_usd":      0.0021
    }
    /* ... more steps ... */
  ],
  "usage": {
    "input_tokens":  18230,
    "output_tokens":  1840,
    "cost_usd":      0.0312,
    "wall_seconds":  41.8,
    "tool_calls":    4
  },
  "failure": null   // populated only when status='failed'
}
```

#### 8.1.3 System prompt template (built by the runtime)

```
You are {identity}.

Your task:
{goal}

Available tools:
{tool_descriptions}        // built from each tool node's metadata

Memory (carried across runs):
{memory_snapshot}

Loop policy:
- You may call tools as many times as needed, up to {max_iterations}.
- When done, respond with a final JSON object summarising what you did.
- If you cannot accomplish the task with the available tools, respond
  with {"status": "blocked", "reason": "..."} and stop.

Constraints:
- Never call a tool that's not in your list.
- Never invent tool arguments — read each tool's schema.
- If a tool call fails twice, switch strategy or stop.

{skills}
```

### 8.2 Tool registry

#### 8.2.1 Building tool schemas from `NodeMetadata`

Every existing node already has a `NodeMetadata.properties[]` that
describes its inputs. The tool registry walks each tool node and emits
a JSON-schema the LLM can speak:

```python
def build_tool_schema(node_def: NodeDefinition) -> dict:
    return {
        "name":        node_def.type.replace(".", "_"),
        "description": node_def.description,
        "input_schema": {
            "type": "object",
            "properties": {
                p["name"]: _property_to_jsonschema(p)
                for p in node_def.properties
                if not p.get("hidden")
            },
            "required": [
                p["name"] for p in node_def.properties
                if p.get("required")
            ]
        }
    }
```

Field-type mapping:

| RunMyCrew property type | JSON-schema |
|------------------------|-------------|
| `string` | `{ "type": "string" }` |
| `number` | `{ "type": "number" }` |
| `boolean` | `{ "type": "boolean" }` |
| `options` | `{ "type": "string", "enum": [...] }` |
| `json` | `{ "type": "object" }` |
| `credential` | excluded (auto-injected from the tool node's connection) |
| `media` / `gdrive-folder` etc. | reduced to id strings |

#### 8.2.2 Tool execution

```python
async def execute_tool(tool_name: str, args: dict, ctx: NodeContext) -> Any:
    node_id = tool_registry[tool_name]
    node    = workflow.find_node(node_id)
    return await node.execute(input_data=args, context=ctx)
```

The agent's credential set is injected via `ctx`. Sandbox the call so
the tool can't reach unrelated nodes (no `ctx.workflow.find_node`).

#### 8.2.3 Per-tool permission toggle (UI)

Each tool entry in the inspector has three toggles:

| Toggle | Effect |
|--------|--------|
| `enabled` | Tool appears in the schema. Default ON. |
| `requires_confirmation` | LLM may call but the runtime pauses for human review. (Phase post-v1.) |
| `rate_limit` | Max N calls per loop fire. Default unlimited. |

### 8.3 ReAct runtime

#### 8.3.1 Loop body

```python
async def run_react_loop(props, ctx, tool_registry, budget) -> AgentLoopResult:
    messages = [system_prompt(props), user_prompt(props.goal)]
    trace = []
    iteration = 0

    while True:
        # Budget checks (hard cutoffs)
        if budget.iter_exceeded(iteration): return result("budget_exhausted")
        if budget.time_exceeded():          return result("budget_exhausted")
        if budget.tokens_exceeded():        return result("budget_exhausted")
        if budget.cost_exceeded():          return result("budget_exhausted")

        # Step the LLM
        resp = await llm.complete(
            messages=messages,
            tools=tool_registry.schemas(),
            temperature=props.temperature,
        )
        budget.add_llm(resp.usage)

        # Branch on tool vs final
        if resp.tool_calls:
            for call in resp.tool_calls:
                tool_result = await tool_registry.execute(call.name, call.args, ctx)
                messages.extend([resp.assistant_msg, tool_msg(call, tool_result)])
                trace.append(make_step(iteration, resp, call, tool_result))
                stream_to_frontend(trace[-1])
        else:
            # Final response
            messages.append(resp.assistant_msg)
            final = parse_final(resp.content)
            trace.append(make_final_step(iteration, resp, final))
            stream_to_frontend(trace[-1])

            if iteration < props.min_iterations:
                messages.append(user_msg("Re-evaluate; min_iterations not met."))
                iteration += 1
                continue

            if not matches_success_when(final, props.success_when):
                messages.append(user_msg("Re-evaluate; success condition not met."))
                iteration += 1
                continue

            return AgentLoopResult(status="success", result=final, trace=trace)

        iteration += 1
```

#### 8.3.2 Edge cases

| Case | Handling |
|------|----------|
| LLM hallucinates a tool name | Reject with error observation, count as iteration |
| LLM emits malformed JSON tool args | Reject with error observation |
| Tool node raises | Append `{error: str}` as observation; continue the loop |
| Tool returns >10MB | Truncate with `[truncated]` marker before feeding back |
| LLM tries to recurse into itself | Block; the AgentLoop is not its own tool |
| `success_when` JSONata invalid | Treat as "no condition"; warn on workflow save |
| LLM returns malformed final JSON | Wrap in `{"raw_response": "..."}` and continue |

### 8.4 Budget enforcer

```python
@dataclass
class Budget:
    max_iterations:  int
    max_seconds:     int
    max_input_tokens: int
    max_cost_usd:    float

    used_tokens:  int = 0
    used_cost:    float = 0
    started_at:   datetime = field(default_factory=lambda: datetime.now(UTC))

    def iter_exceeded(self, n): return n >= self.max_iterations
    def time_exceeded(self):    return (datetime.now(UTC) - self.started_at).total_seconds() >= self.max_seconds
    def tokens_exceeded(self):  return self.used_tokens >= self.max_input_tokens
    def cost_exceeded(self):    return self.used_cost >= self.max_cost_usd

    def add_llm(self, usage):
        self.used_tokens += usage.input_tokens
        self.used_cost   += compute_cost(usage)
```

Cost computation respects the LLM provider's per-model pricing table
(stored in `apps/api/app/features/billing/pricing.py`, new file).

### 8.5 Concurrency mutex

Redis-backed, workflow-scoped.

#### 8.5.1 Key format

```
runmycrew:concurrency:workflow:{workflow_id}
```

#### 8.5.2 Operations

```python
async def acquire(workflow_id: str, ttl_seconds: int) -> AcquireResult:
    key = f"runmycrew:concurrency:workflow:{workflow_id}"
    token = uuid4().hex
    ok = await redis.set(key, token, ex=ttl_seconds, nx=True)
    return AcquireResult(ok=ok, token=token if ok else None)

async def release(workflow_id: str, token: str) -> bool:
    # Lua: only delete if value matches token (don't release someone else's lock)
    return await redis.eval(RELEASE_SCRIPT, keys=[key], args=[token])
```

#### 8.5.3 Policy

| Policy | When `acquire` returns `ok=False` |
|--------|-------------------------------------|
| `skip` (default) | Log `skipped_concurrent`, exit, no run record (or exit-only audit) |
| `queue` | Sleep 5s + retry up to `max_seconds`, then `skip` |
| `replace` | Force-release the existing lock, kill the in-flight run, acquire |

TTL is `max_seconds + 60` so a crashed worker's lock auto-expires.

### 8.6 Trace persistence

#### 8.6.1 Per-step schema (stored as JSONB in run record)

```jsonc
{
  "step":              0,
  "iteration":         1,
  "thought":           "I should list the open bugs first",
  "tool_call": {
    "name":            "linear_list_issues",
    "args":            { "queue": "Bug" }
  },
  "tool_result":       { /* truncated to 50KB */ },
  "tool_duration_ms":  423,
  "tool_error":        null,
  "tokens_in":         1820,
  "tokens_out":        87,
  "cost_usd":          0.0021,
  "started_at":        "2026-06-21T13:00:01.123Z",
  "ended_at":          "2026-06-21T13:00:01.546Z"
}
```

#### 8.6.2 Truncation policy

A single trace step's `tool_result` is capped at 50 KB JSON. If the
real result is larger, the runtime stores:

```jsonc
"tool_result": {
  "__truncated": true,
  "preview":     "<first 5KB>",
  "ref":         "asset://run/{run_id}/step/{step}/result.json"
}
```

The full result is uploaded to the same object storage we already use
for asset uploads.

#### 8.6.3 Aggregate row in `runs` table

```sql
ALTER TABLE runs ADD COLUMN agent_trace JSONB;
ALTER TABLE runs ADD COLUMN agent_usage JSONB;
```

`agent_trace` stores the full trace array. `agent_usage` stores the
roll-up: total tokens, total cost, iterations, tool_calls.

### 8.7 Memory layer

Two distinct layers; both already partially exist.

#### 8.7.1 In-loop messages

Lives only inside one loop fire. Not persisted (the trace IS the
persistence). Held in Python memory during the loop.

#### 8.7.2 Cross-run memory

`MemoryNode` already provides this. Each loop's `memory_key` namespaces
a small k/v store backed by Redis. Two access methods:

- **Automatic snapshot** injected into the system prompt:

  ```
  Memory:
  - last_processed_id: ENG-2701
  - last_seen_count:    14
  ```

  The runtime calls `memory_provider.snapshot(memory_key)` and stringifies.

- **Tool-mediated set**: the agent calls `memory.set(key, value)` like
  any other tool. We expose `memory.get(key)` + `memory.set(key, value)`
  as built-in tools when `memory_key` is set.

### 8.8 Failure handler

Three policies + their behaviour:

| Policy | What happens after `failed` |
|--------|------------------------------|
| `silent` | Run record marks failed; no further action |
| `retry` | Runner re-fires the loop after backoff (1m / 5m / 30m); after `retry_count` exhausted, falls through to `silent` |
| `escalate` | Runner POSTs to a per-workspace `escalation_endpoint` configured under Settings → Automations → Escalation. Default endpoint posts to a Slack channel chosen at config time. |

Escalation payload:

```jsonc
{
  "workflow_id":   "wf_...",
  "workflow_name": "Triage Linear bugs",
  "run_id":        "run_...",
  "run_url":       "https://app.runmycrew.com/runs/run_...",
  "status":        "failed",
  "failure":       { "step": 3, "reason": "linear.update_issue: 401" },
  "started_at":    "...",
  "ended_at":      "...",
  "usage":         { /* ... */ },
  "trace_summary": "Listed bugs, picked ENG-2701, tried to set label, 401"
}
```

---

## 9. Data model

### 9.1 Postgres migrations

```sql
-- Phase 1
ALTER TABLE runs ADD COLUMN agent_trace      JSONB;
ALTER TABLE runs ADD COLUMN agent_usage      JSONB;
ALTER TABLE runs ADD COLUMN concurrency_status TEXT;   -- 'ok'|'skipped'|'queued'|'replaced'

-- Phase 2
CREATE TABLE workflow_concurrency_config (
    workflow_id      UUID    PRIMARY KEY REFERENCES workflows(id) ON DELETE CASCADE,
    policy           TEXT    NOT NULL DEFAULT 'skip'   -- 'skip'|'queue'|'replace'
        CHECK (policy IN ('skip','queue','replace')),
    queue_max_wait_seconds INTEGER NOT NULL DEFAULT 60
);

-- Phase 5
ALTER TABLE workflows ADD COLUMN cron_drift_policy TEXT NOT NULL DEFAULT 'latest';
    -- 'latest' | 'catchup' | 'skip'

-- Phase 1 (escalation handler config — workspace level)
CREATE TABLE workspace_escalation_config (
    workspace_id        UUID    PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
    slack_channel_id    TEXT,
    slack_credential_id UUID    REFERENCES credentials(id) ON DELETE SET NULL,
    email_to            TEXT,
    webhook_url         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 9.2 Redis keys

| Key | TTL | Value | Purpose |
|-----|-----|-------|---------|
| `runmycrew:concurrency:workflow:{workflow_id}` | `max_seconds + 60` | uuid token | Concurrency lock |
| `runmycrew:agent_memory:{workspace_id}:{memory_key}` | none (manual delete) | json blob | Cross-run memory |
| `runmycrew:agent_budget:{run_id}` | `max_seconds + 60` | json | Live budget tracking (for SSE display) |
| `runmycrew:agent_step_stream:{run_id}` | 1h | redis-stream | Trace step pub/sub |

### 9.3 Object storage

Trace step results >50KB are stored at:

```
{S3_PREFIX}/runs/{workspace_id}/{run_id}/step/{step}/result.json
```

Lifecycle: 30 days (matches run history retention).

---

## 10. API surfaces

### 10.1 HTTP endpoints (new)

| Method | Path | Body | Returns |
|--------|------|------|---------|
| GET | `/api/v1/runs/{run_id}/trace` | — | `Trace[]` for the run |
| GET | `/api/v1/runs/{run_id}/trace/{step}/result` | — | Full step result (de-truncated) |
| POST | `/api/v1/workflows/{wf_id}/concurrency-config` | `{policy, queue_max_wait_seconds}` | new config |
| GET | `/api/v1/workspaces/{ws_id}/escalation-config` | — | config |
| PUT | `/api/v1/workspaces/{ws_id}/escalation-config` | `EscalationConfig` | updated config |

### 10.2 SSE events (extending existing `/runs/{id}/events`)

New event types:

```jsonc
// emitted whenever the loop publishes a trace step
{
  "type": "agent_loop_step",
  "step": { /* same shape as 8.6.1 */ }
}

// emitted on iteration boundary
{
  "type": "agent_loop_iteration",
  "iteration": 3,
  "usage_so_far": { /* ... */ }
}

// terminal events
{ "type": "agent_loop_success",         "result": { /* ... */ } }
{ "type": "agent_loop_budget_exhausted", "limit": "iter|time|tokens|cost" }
{ "type": "agent_loop_failed",          "error": { /* ... */ } }
```

### 10.3 Internal Python APIs

```python
# apps/api/app/node_system/nodes/ai/agent_loop/runtime.py

class AgentLoopRuntime:
    def __init__(self, props: AgentLoopProperties, ctx: NodeContext): ...
    async def run(self) -> AgentLoopResult: ...
    async def cancel(self) -> None: ...

# apps/api/app/execution_engine/concurrency.py

class ConcurrencyManager:
    async def acquire(self, workflow_id: UUID, ttl: int) -> AcquireResult: ...
    async def release(self, workflow_id: UUID, token: str) -> bool: ...
    async def policy_for(self, workflow_id: UUID) -> ConcurrencyPolicy: ...

# apps/api/app/features/agent_trace/persistence.py

class TracePersistence:
    async def append_step(self, run_id: UUID, step: TraceStep) -> None: ...
    async def finalize(self, run_id: UUID, usage: Usage) -> None: ...
    async def get_trace(self, run_id: UUID) -> list[TraceStep]: ...
```

---

## 11. Frontend UX

### 11.1 Inspector (agent_loop node selected)

Three-tab inspector replaces the current single-column inspector when
the selected node is `ai.agent_loop`.

```
┌─────────────────────────────────────────────────────┐
│ ▢  Agent Loop                                       │
├─────────────────────────────────────────────────────┤
│  Goal   │  Tools   │  Limits                       │
│ ────────┴──────────┴──────────                     │
│                                                     │
│  Goal tab                                           │
│  ────────                                           │
│  Goal (plain English)                               │
│  ┌─────────────────────────────────────────────┐   │
│  │ Triage new bug reports in the Bug queue...  │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Identity         [RunMyCrew Triage Bot]            │
│  LLM credential   [OpenAI · GPT-5 ▾]                │
│  Skills           [triage-tone ✕] [+ Add skill]     │
│  Memory key       [linear-triage]                   │
│  Success when     [$.action_taken == true]          │
└─────────────────────────────────────────────────────┘
```

```
│  Tools tab                                          │
│  ─────────                                          │
│  Drag nodes from the canvas here to expose them    │
│  as tools the agent can call.                       │
│                                                     │
│  ☑  linear.list_issues       [×]                   │
│  ☑  linear.update_issue      [×]   max 5/loop      │
│  ☑  slack.post_message       [×]                   │
│  ☐  github.create_pr         [×]   ← disabled      │
│                                                     │
│  + Drop a node here                                 │
```

```
│  Limits tab                                         │
│  ──────────                                         │
│  Max iterations            [ 10 ]                   │
│  Max wall-clock seconds    [ 600 ]                  │
│  Max input tokens          [ 100,000 ]              │
│  Max cost per fire         [ USD 0.50 ]             │
│                                                     │
│  On failure                 ◉ Escalate              │
│                             ◯ Retry                 │
│                             ◯ Silent                │
│                                                     │
│  Concurrency                ◉ Skip if running       │
│                             ◯ Queue (up to 5)       │
│                             ◯ Replace               │
└─────────────────────────────────────────────────────┘
```

### 11.2 Logs panel — trace timeline

When viewing a run for an `agent_loop` node, the logs panel switches
from "JSON tree per node" to "trace timeline."

```
┌──────────────────────────────────────────────────────────────┐
│   Run #1842  ·  Triage Linear bugs  ·  ✅ success  ·  $0.03  │
│   started 13:00:01  ·  ended 13:00:43  ·  4 iterations       │
├──────────────────────────────────────────────────────────────┤
│  Iteration 1 ─────────────────────────────────────────────── │
│  🧠  I should list the open bugs first.                     │
│  🛠  linear_list_issues({"queue":"Bug"})         ◷ 423 ms   │
│       → 3 items returned ▾                                  │
│                                                              │
│  Iteration 2 ─────────────────────────────────────────────── │
│  🧠  ENG-2701 looks like a backend P1; let me label.        │
│  🛠  linear_update_issue({id:"ENG-2701",                    │
│         labels:["backend"], priority:"P1"})    ◷ 188 ms   │
│       → ok ▾                                                │
│                                                              │
│  Iteration 3 ─────────────────────────────────────────────── │
│  🧠  ENG-2703 is a frontend bug, P2.                        │
│  🛠  linear_update_issue({...})                ◷ 161 ms   │
│       → ok ▾                                                │
│                                                              │
│  Iteration 4 ─────────────────────────────────────────────── │
│  ✅  Final: {                                                │
│       action_taken: true,                                    │
│       summary: "Triaged 3 bugs, all labeled + prioritised"   │
│      }                                                       │
└──────────────────────────────────────────────────────────────┘
```

Each tool row collapses to show full args + raw result via the existing
`JsonTreeView`. Live-updates over SSE while the loop is in flight.

### 11.3 Loops dashboard (workspace-level)

(Phase post-v1.) A page at `/loops` showing every workflow that has an
`agent_loop` node, with last-run status, last-7-days cost, success
rate, and a "View trace" deep-link.

### 11.4 Loop templates page

Under `Templates → Agent Loops`, the three starter templates with:

- One-line description
- Required credentials checklist
- Expected cost ("≈$0.03 per fire")
- Expected schedule ("every 30 minutes")
- A `Try this` button that imports the template into the user's
  workspace as a draft workflow.

---

## 12. Templates

Complete JSON for each starter loop. Lives at
`apps/site/src/features/templates/data/loop-templates.ts` and (for the
backend importer) `apps/api/app/features/templates/seeds/loops/`.

### 12.1 Triage Linear bugs

```jsonc
{
  "id":   "loop_linear_triage",
  "name": "Triage new Linear bugs",
  "summary": "Every 30 minutes, scans the Bug queue and labels + prioritises any unclassified issues. P0 bugs are also posted to #oncall.",
  "category": "loops",
  "estimated_cost_per_fire": "USD 0.02–0.05",
  "schedule": "every 30 minutes",
  "credentials_required": ["linear", "slack"],
  "nodes": [
    { "id": "trigger", "type": "common.cron",
      "data": { "cron_expression": "*/30 * * * *" } },
    { "id": "agent",   "type": "ai.agent_loop",
      "data": {
        "goal": "Triage unlabelled issues in the Bug queue. Pick a label from [frontend, backend, infra, unknown] and a priority from [P0, P1, P2]. If P0, also post to the on-call Slack channel.",
        "tools": ["linear_list", "linear_update", "slack_post"],
        "max_iterations": 8,
        "max_cost_usd":   0.05,
        "memory_key":     "linear-triage",
        "success_when":   "$.action_taken == true",
        "failure_policy": "escalate"
      }
    },
    { "id": "linear_list",   "type": "action.linear.list_issues" },
    { "id": "linear_update", "type": "action.linear.update_issue" },
    { "id": "slack_post",    "type": "action.slack.post_message" }
  ],
  "edges": [
    { "source": "trigger", "target": "agent" }
  ]
}
```

### 12.2 Dependabot auto-merger

```jsonc
{
  "id":   "loop_dependabot_automerge",
  "name": "Auto-merge Dependabot PRs",
  "summary": "Fires on every new pull request. If author is Dependabot, the bump is patch/minor, and CI is green, merges automatically. Otherwise posts to #dependencies for human review.",
  "category": "loops",
  "estimated_cost_per_fire": "USD 0.01–0.02",
  "schedule": "GitHub webhook · pull_request.opened",
  "credentials_required": ["github", "slack"],
  "nodes": [
    { "id": "trigger", "type": "http.webhook" },
    { "id": "agent",   "type": "ai.agent_loop",
      "data": {
        "goal": "Decide whether to merge this PR. Auto-merge only if: author == 'dependabot[bot]' AND version bump is 'patch' or 'minor' AND all required checks are green. Otherwise post the PR title + link to the dependencies Slack channel.",
        "tools": ["github_get_pr", "github_get_checks", "github_merge_pr", "slack_post"],
        "max_iterations": 6,
        "max_cost_usd":   0.05,
        "success_when":   "$.action == 'merged' or $.action == 'escalated'",
        "failure_policy": "escalate"
      }
    },
    /* tool nodes ... */
  ],
  "edges": [
    { "source": "trigger", "target": "agent" }
  ]
}
```

### 12.3 Sentry → GitHub issue

```jsonc
{
  "id":   "loop_sentry_to_github",
  "name": "Sentry → GitHub issue",
  "summary": "Every 15 minutes, fetches new Sentry issues. For each, checks if a GitHub issue already references the fingerprint. If not, creates a new issue with the stack trace + frequency.",
  "category": "loops",
  "estimated_cost_per_fire": "USD 0.01–0.03",
  "schedule": "every 15 minutes",
  "credentials_required": ["sentry", "github"],
  "nodes": [
    /* ... */
    { "id": "agent", "type": "ai.agent_loop",
      "data": {
        "goal": "For each new Sentry issue (newer than the timestamp in memory.last_seen_at), check if a GitHub issue already mentions the fingerprint. If not, create one with title, stack trace, and frequency. Update memory.last_seen_at to the newest issue's timestamp.",
        "tools": ["sentry_list", "github_search_issues", "github_create_issue",
                  "memory_get", "memory_set"],
        "memory_key": "sentry-bridge",
        "max_iterations": 12,
        "max_cost_usd":   0.05,
        "success_when":   "$.action_taken == true or $.no_new_issues == true",
        "failure_policy": "escalate"
      }
    }
    /* ... */
  ]
}
```

---

## 13. Implementation phases

Each phase is a separate PR. Phases are ordered so each lands a useful,
shippable slice.

### Phase 1 — Hardening the existing `ai.agent` node (P0)

**Goal:** A user wiring an existing `ai.agent` behind a cron can run a
loop that stops cleanly, has bounded cost, and persists a trace.

**Files touched:**

```
apps/api/app/node_system/nodes/ai/agent/agent.py
apps/api/app/node_system/nodes/ai/agent/runtime.py         (new)
apps/api/app/node_system/nodes/ai/agent/budget.py          (new)
apps/api/app/node_system/nodes/ai/agent/trace.py           (new)
apps/api/app/features/runs/models.py                       (+ agent_trace, agent_usage)
apps/api/alembic/versions/{...}_runs_agent_trace.py        (new migration)
apps/api/app/features/runs/repository.py                   (persist trace)
apps/api/tests/node_system/ai/agent/test_loop_runtime.py   (new)
apps/api/tests/node_system/ai/agent/test_budget.py         (new)
```

**Deliverables:**
- `success_when` JSONata expression evaluated against final result.
- Hard budgets: `max_iterations`, `max_seconds`, `max_input_tokens`,
  `max_cost_usd` enforced as cutoffs.
- Structured `trace[]` schema (8.6.1) emitted to run record.
- `failure_policy` field (`silent` / `retry` / `escalate`).
- Cost computation table per LLM model (`pricing.py`).
- Comprehensive tests for budget edge cases.

**Estimated effort:** 3 days.

### Phase 2 — Concurrency mutex (P0)

**Goal:** Two cron fires can't run the same workflow at the same time.

**Files touched:**

```
apps/api/app/execution_engine/concurrency.py               (new)
apps/api/app/execution_engine/engine/workflow_runner.py    (use it)
apps/api/app/features/workflows/models.py                  (concurrency_config)
apps/api/alembic/versions/{...}_workflow_concurrency.py    (new migration)
apps/api/tests/execution_engine/test_concurrency.py        (new)
```

**Deliverables:**
- Redis-backed acquire/release with token-based safe release.
- Workflow-level `concurrency_policy` (skip / queue / replace).
- Run record `concurrency_status` column.
- Integration test that fires the same workflow twice in parallel and
  asserts the second is skipped or queued.

**Estimated effort:** 1.5 days.

### Phase 3 — Trace viewer in the logs panel (P1)

**Goal:** Users can see the agent's reasoning + tool calls as they
happen, chat-style.

**Files touched:**

```
apps/api/app/features/runs/sse.py                          (+ agent_loop_step event)
apps/web/src/features/workflow-editor/components/right-panel/panels/LogsPanel.tsx
apps/web/src/features/workflow-editor/components/right-panel/panels/logs/AgentTraceTimeline.tsx  (new)
apps/web/src/features/workflow-editor/hooks/useAgentTrace.ts                                     (new)
apps/web/src/features/workflow-editor/types/agentTrace.ts                                        (new)
```

**Deliverables:**
- SSE `agent_loop_step` event emitted by the runtime.
- React hook that subscribes + buffers steps.
- Timeline component (collapsible thought / tool / result rows).
- Cost + iteration counter chip in the header.

**Estimated effort:** 2 days.

### Phase 4 — Tool registry polish (P1)

**Goal:** Dropping a node into the `tools` array Just Works. No manual
schema editing.

**Files touched:**

```
apps/api/app/node_system/tools/registry.py                 (new)
apps/api/app/node_system/tools/schema.py                   (new — NodeMetadata → JSON schema)
apps/api/app/node_system/nodes/ai/agent/runtime.py         (use registry)
apps/api/tests/node_system/tools/test_registry.py          (new)
apps/web/src/features/workflow-editor/components/inspector/components/AgentToolsTab.tsx   (new)
```

**Deliverables:**
- Auto-build JSON-schema for any tool node from its `NodeMetadata`.
- Per-tool `enabled` + `max_calls_per_loop` toggles.
- Inspector tab with drag-from-canvas tool list.
- Tests that build schemas for 10 representative nodes.

**Estimated effort:** 2 days.

### Phase 5 — Cron drift policy (P2)

**Goal:** When a cron fire is late, the platform behaves predictably.

**Files touched:**

```
apps/api/app/execution_engine/scheduler/cron.py            (modify)
apps/api/app/features/workflows/models.py                  (+ cron_drift_policy)
apps/api/alembic/versions/{...}_cron_drift_policy.py       (new migration)
apps/api/tests/execution_engine/test_cron_drift.py         (new)
```

**Deliverables:**
- `cron_drift_policy` field: `latest` (default — fire once for the
  current tick), `catchup` (fire for every missed tick), `skip` (don't
  fire if more than 1 tick was missed).
- Cron scheduler reads the policy.

**Estimated effort:** 1 day.

### Phase 6 — Escalation handler + starter templates (P2)

**Goal:** "Failure routes to my Slack channel" works out of the box,
and users have three working starter loops to copy from.

**Files touched:**

```
apps/api/app/features/escalation/                          (new feature module)
apps/api/app/features/escalation/service.py                (new)
apps/api/app/features/escalation/router.py                 (new)
apps/api/app/features/templates/seeds/loops/triage_linear_bugs.json   (new)
apps/api/app/features/templates/seeds/loops/dependabot_automerge.json (new)
apps/api/app/features/templates/seeds/loops/sentry_to_github.json     (new)
apps/site/src/app/templates/loops/page.tsx                 (new gallery page)
apps/web/src/features/settings/components/EscalationConfig.tsx        (new settings card)
```

**Deliverables:**
- Workspace-level escalation config (Slack channel + creds).
- Built-in handler that the agent runtime calls when
  `failure_policy=escalate`.
- Three starter templates importable from the templates gallery.
- A 30-second screencast embedded next to each template.

**Estimated effort:** 2 days.

### Phase 7 — Docs + marketing (P2)

**Goal:** A user finds + understands loop engineering in <5 minutes.

**Files touched:**

```
apps/site/src/app/docs/agent-loops/page.tsx                (new docs page)
apps/site/src/features/marketing/components/LoopsSection.tsx          (new homepage section)
apps/site/src/features/blog/data/posts.ts                  (+ "Introducing Agent Loops" post)
apps/site/src/features/marketing/data/site.ts              (+ nav entry)
```

**Estimated effort:** 1 day.

### Totals

| Phase | Effort |
|-------|--------|
| 1 — Agent hardening | 3 days |
| 2 — Concurrency | 1.5 days |
| 3 — Trace viewer | 2 days |
| 4 — Tool registry polish | 2 days |
| 5 — Cron drift | 1 day |
| 6 — Escalation + templates | 2 days |
| 7 — Docs + marketing | 1 day |
| **Total** | **12.5 working days** |

---

## 14. Testing strategy

### 14.1 Unit tests

- Budget enforcement: every cutoff path (iter / time / tokens / cost).
- `success_when` evaluation against valid + invalid JSONata.
- Tool schema builder against representative node types.
- Concurrency manager: acquire/release, expired lock, contested
  acquire.
- Cost table accuracy per LLM model.

### 14.2 Integration tests

- End-to-end loop with a fake LLM that:
  - returns 1 tool_call then a final response → assert success.
  - returns 11 tool_calls → assert `budget_exhausted`.
  - returns malformed JSON → assert one retry then surface.
  - returns nonexistent tool name → assert error observation, continue.
- Two concurrent runs of the same workflow → assert second is skipped.
- Failure → escalation → assert payload posted to mock Slack webhook.

### 14.3 Property tests (Hypothesis)

- Trace serialization round-trips (build trace → JSON → parse → equal).
- Tool schema is always valid JSON-schema regardless of node metadata.

### 14.4 Manual QA checklist (one per phase)

- [ ] Build the Linear triage template, fire it manually, watch trace.
- [ ] Wait for cron to fire it three times; assert no overlap.
- [ ] Disable Linear credentials → assert escalation message lands.
- [ ] Hit the cost cap; assert exit `budget_exhausted` + record shows
  partial trace.

### 14.5 Load testing

- 50 concurrent loop fires across 10 workflows, sustained 10 min.
- Assert: no runner deadlocks, P99 trace persistence <500 ms, no
  redis-key leaks.

---

## 15. Migration plan

### 15.1 Backward compatibility

- Existing `ai.agent` node keeps its current single-pass semantics
  by default. The new fields (`success_when`, `max_cost_usd`,
  `failure_policy`) are all optional with safe defaults.
- Existing workflows do **not** auto-migrate to `ai.agent_loop`.
- The new `ai.agent_loop` node is a strict superset; we may eventually
  deprecate `ai.agent` but not before v2.

### 15.2 Database migrations

Three migrations land across Phase 1, 2, 5:

```
alembic/versions/{ts}_runs_agent_trace.py
alembic/versions/{ts}_workflow_concurrency.py
alembic/versions/{ts}_cron_drift_policy.py
```

Each is forward-only + zero-downtime (only `ADD COLUMN NULL` + new
table creates).

### 15.3 Feature flag

A workspace-level flag `agent_loop_enabled` (default `false` in prod
for the first week, then flipped per workspace) gates:

- The `ai.agent_loop` node showing up in the node library.
- The escalation config card.
- The loops dashboard.

Flag check happens in:

```python
apps/api/app/features/feature_flags/service.py  (existing)
```

### 15.4 Rollout sequence

| Day | Step |
|-----|------|
| Day 0 | Phase 1+2 land behind flag; smoke test on staging. |
| Day 3 | Enable flag on 1 workspace (Bibek's). Dogfood for 48h. |
| Day 5 | Enable on first 5 beta workspaces. |
| Day 10 | Enable Phase 3 (trace viewer) for beta workspaces. |
| Day 12 | Phase 4 + 5 land. |
| Day 15 | Phase 6 (templates) lands; flip flag on for all workspaces. |
| Day 16 | Phase 7 (docs + blog post) ships. |

---

## 16. Operational concerns

### 16.1 Cost

Per-loop cost is bounded by `max_cost_usd`. The platform tracks:

| Layer | What's tracked | Where |
|-------|---------------|-------|
| Per-run | `agent_usage` JSONB on run record | DB |
| Per-workflow daily | rollup view `daily_workflow_cost` | DB |
| Per-workspace monthly | rollup view `monthly_workspace_cost` | DB |

Workspace billing tier sets a soft cap; hitting 90% triggers an email
to workspace owners. Hitting 100% pauses cron-triggered loops (webhook
loops still fire) until next billing cycle or upgrade.

### 16.2 Observability

- Every loop run emits structured log lines with
  `workspace_id`, `workflow_id`, `run_id`, `iteration`, `tool_name`,
  `cost_usd`. Existing logger config.
- Sentry receives any uncaught exception inside the runtime.
- A Grafana / Glitchtip dashboard (post-v1) shows: loop fire rate,
  success rate, p50/p95 wall-clock, p50/p95 cost.

### 16.3 Security

- Tool credentials are scoped to the loop's workspace. The agent
  cannot reach credentials from another workspace even if the LLM
  references them by name.
- LLM responses are never `eval`-ed. Tool args are JSON-schema-validated
  before execution.
- The runtime sandboxes tool execution exactly like every other node:
  same `NodeContext`, same network rules, same secret redaction in
  logs.
- Memory contents are never sent to the LLM beyond the snapshot the
  runtime explicitly injects.
- Trace results larger than 50 KB are stored in object storage with
  the run's `workspace_id` in the key — RBAC-checked on retrieval.

### 16.4 Rate limits

The runtime respects per-tool rate limits (`max_calls_per_loop`) and
per-provider LLM rate limits (back-off + retry).

Loop fires that hit the LLM provider's rate limit fail-soft into
`failure_policy`.

### 16.5 Data retention

- Trace step bodies (per 8.6.2 truncation): 30 days in object storage,
  matching run history.
- Trace summary metadata: kept with the run record per plan retention.

---

## 17. Performance budget

| Metric | Target (P95) |
|--------|--------------|
| Loop dispatcher → runtime start latency | < 200 ms |
| Trace step write (DB upsert) | < 50 ms |
| SSE event lag (server → browser) | < 250 ms |
| Concurrency `acquire` → `release` overhead | < 20 ms |
| Tool call round-trip (excl. provider time) | < 50 ms |
| Cold-start LLM call (Anthropic) | < 2 s |

Loop run wall-clock at P95 must be ≤ `max_seconds`. The budget enforcer
hard-cuts above this regardless.

---

## 18. Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM hallucinates a destructive tool call | High | High | Per-tool rate limit; `requires_confirmation` for destructive tools (post-v1) |
| Runaway cost (budget bypass bug) | Med | High | Hard-cut tested per-LLM-call AND post-call; provider-side cap as a backstop |
| Memory grows unbounded | Low | Med | Memory key gets a soft cap (1 MB) + auto-truncate-by-LRU strategy |
| Concurrent runs both pass acquire | Low | Med | Lua-script release verifies token; integration tests cover this |
| Trace JSON column bloats run table | High | Low | 50 KB per step + 10 MB total per run cap; overflow goes to S3 |
| LLM provider outage stalls every loop | Med | Med | `failure_policy=escalate` posts to Slack; next cron tick retries naturally |
| User configures a private memory key with PII | Med | Med | Add a "memory contents are sent to your LLM provider" warning on the inspector |
| Misconfigured `success_when` causes infinite loops | Low | Med | Hard `max_iterations` always wins; UI validates JSONata syntax on save |

---

## 19. Open questions

Reviewers should answer or push back on each.

1. **Concurrency default policy** — proposed `skip`. Alternatives: per
   workflow opt-in, default `queue`. Trade-off: `skip` is safest;
   `queue` is friendlier for ops-style loops where you don't want to
   miss work.

2. **Hard vs soft budgets** — proposed hard. Soft would log a warning
   + continue. Hard is safer; soft is more forgiving but harder to
   reason about. Recommend hard for v1; revisit if users complain.

3. **Trace storage strategy**:
   - **A.** Always store full trace.
   - **B.** Always store; truncate per-step at 50 KB.
   - **C.** Per-workspace policy.
   - Proposed: **B**. Adopt **C** post-v1 if needed.

4. **Failure escalation default** — proposed: workspace-level config
   one-off, default Slack channel `#runmycrew-alerts`. Alternative:
   user explicitly picks per loop. Trade-off: workspace-level is fewer
   clicks per loop; per-loop is more granular.

5. **MCP bundling** — proposed: NONE in v1. Users wire MCP servers
   themselves via the existing `mcpServers` field. Bundling
   (filesystem, web search) is post-v1.

6. **Cost attribution to billing** — proposed: track `cost_usd` but
   don't bill until v2 (we're still in beta tier). Show the cost in
   the trace viewer + monthly digest so users see the meter running.

7. **Tool execution sandboxing** — proposed: same context as the
   parent workflow's other nodes (same credentials, same network).
   Alternative: tighter sandbox per tool. Trade-off: tighter sandbox
   = more work; for v1 the parity is fine.

8. **Naming** — `ai.agent_loop` vs renaming the existing `ai.agent` to
   `ai.agent_single` and reusing `ai.agent` for the loop variant.
   Proposed: keep `ai.agent`, add `ai.agent_loop`. Renaming hits
   existing workflows.

---

## 20. Non-goals

Explicitly NOT in v1. Each may land later — flagged with phase guess.

| Non-goal | Why deferred | Likely phase |
|----------|--------------|--------------|
| Multi-agent debate / consensus / hand-off | Single-agent loops haven't been validated yet | v2 |
| Code-writing primitive (open PR / commit) | Single sub-workflow can compose this | v2 |
| Separate billing tier for loops | Cost tracking lands first; tier comes once we have data | v2 |
| Custom user-defined ReAct prompts | One good ReAct prompt validated first | v2 |
| Voice / Telegram triggers | Not unique to loops; ships as regular triggers | TBD |
| LLM-as-judge for the `success_when` check | JSONata is enough for v1 | v2 |
| Cross-workspace loops | Conflicts with tenancy model; not requested yet | maybe never |
| Built-in MCP servers (filesystem, web) | BYO via existing `mcpServers` field works | v2 |
| Workflow versioning + rollback for loops | General workflow versioning lands first | v2 |

---

## 21. FAQ

**Q: Why not just use LangChain / CrewAI / AutoGen?**
A: We already have a workflow engine, credential management,
integrations, and a UI. Bolt-on agent frameworks would conflict with
each of those. The agent loop is a node in our existing graph —
fewer new abstractions, more integration leverage.

**Q: Is this the same as "AI workflow generation" (Crew AI)?**
A: No. Crew AI helps the user *design* a workflow. Loop engineering
*runs* a workflow autonomously. Both can coexist — Crew AI can
generate an Agent Loop workflow for the user.

**Q: Can a loop call another loop?**
A: Yes, via the existing `sub_workflow` node. The sub-workflow's
concurrency mutex is independent.

**Q: How do I migrate an existing `ai.agent` workflow to a loop?**
A: For v1 you swap the node type in the JSON and re-save the workflow.
A UI migration tool may ship in v2 if there's demand.

**Q: What happens if the worker process dies mid-loop?**
A: The redis concurrency lock auto-expires after `max_seconds + 60`.
The cron scheduler fires the next tick normally. The interrupted run
ends up with status `failed` + a generic `worker_crash` error. Trace
captured so far is preserved.

**Q: Can the agent run *forever* with `max_iterations = infinity`?**
A: No. `max_iterations` is bounded by a system-wide cap (default 100)
that admins can raise. Even if raised, `max_seconds` + `max_cost_usd`
are independent hard cutoffs.

**Q: Can the loop be paused mid-run for human approval?**
A: Yes — wrap the destructive tool with the existing `human_input`
node (HITL pause). The runtime serialises state and resumes when the
human responds. (Phase post-v1 we may ship `requires_confirmation`
directly on the tool entry.)

**Q: Is the trace public to all workspace members?**
A: Yes, subject to the existing workspace RBAC. Workspace members
with `viewer` role can see trace metadata + tool call shapes; only
`editor` and above can see raw tool result payloads.

**Q: What LLMs are supported?**
A: Same provider set as the existing `ai.agent` node: OpenAI,
Anthropic, Google Gemini, Groq, Together, Mistral, OpenRouter,
DeepSeek, Fireworks, Perplexity, xAI. The runtime uses each provider's
tool-use API where available.

**Q: How are tool failures fed back to the LLM?**
A: As a `tool_result` message with shape
`{ "error": "...", "retry_hint": "..." }`. The LLM is instructed in
the system prompt to either retry, switch strategy, or stop after two
failures of the same tool.

**Q: Will adding a 9th column to `runs` slow queries down?**
A: `agent_trace` is JSONB and not indexed. Run-list queries use the
existing index on `created_at`; they don't `SELECT *`. Adding JSONB
columns is a no-op for hot-path performance.

---

## 22. Code sketches

Reference implementations (NOT meant to land as-is — these are
conversation aids for review).

### 22.1 Runtime

```python
# apps/api/app/node_system/nodes/ai/agent/runtime.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
import json
from typing import Any
from uuid import UUID

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.tools.registry import ToolRegistry
from .budget import Budget
from .trace import TraceCollector
from .stop_condition import evaluate_success_when


@dataclass
class AgentLoopResult:
    status: str            # 'success' | 'budget_exhausted' | 'failed' | 'no_op'
    iterations: int
    result: Any
    trace: list[dict]
    usage: dict
    failure: dict | None = None


class AgentLoopRuntime:
    def __init__(self, props, ctx: NodeContext, llm, tool_registry: ToolRegistry):
        self.props = props
        self.ctx = ctx
        self.llm = llm
        self.tools = tool_registry
        self.budget = Budget(
            max_iterations=props.max_iterations,
            max_seconds=props.max_seconds,
            max_input_tokens=props.max_input_tokens,
            max_cost_usd=props.max_cost_usd,
        )
        self.trace = TraceCollector(ctx.run_id)
        self.memory = ctx.memory_for(props.memory_key) if props.memory_key else None

    async def run(self) -> AgentLoopResult:
        messages = self._initial_messages()
        iteration = 0

        while True:
            # Budget gate
            if self.budget.any_exceeded(iteration):
                return self._budget_exhausted(iteration)

            # LLM step
            try:
                resp = await self.llm.complete(
                    messages=messages,
                    tools=self.tools.schemas(),
                    temperature=self.props.temperature,
                )
            except Exception as exc:
                return self._failed(iteration, "llm_error", str(exc))

            self.budget.add_llm(resp.usage)

            # Branch: tool call or final
            if resp.tool_calls:
                for call in resp.tool_calls:
                    obs = await self._exec_tool(call, iteration)
                    messages.extend([resp.assistant_msg, obs])
                iteration += 1
                continue

            # Final response
            messages.append(resp.assistant_msg)
            final = self._parse_final(resp.content)
            await self.trace.append_final(iteration, resp, final)

            if iteration < self.props.min_iterations:
                messages.append(self._user("Re-evaluate; min_iterations not met."))
                iteration += 1
                continue

            if not evaluate_success_when(self.props.success_when, final):
                messages.append(self._user("Re-evaluate; success condition not met."))
                iteration += 1
                continue

            return AgentLoopResult(
                status="success",
                iterations=iteration + 1,
                result=final,
                trace=await self.trace.collect(),
                usage=self.budget.snapshot(),
            )

    async def _exec_tool(self, call, iteration: int) -> dict:
        try:
            result = await self.tools.execute(call.name, call.args, self.ctx)
            await self.trace.append_step(iteration, call, result, error=None)
            return self._tool_msg(call, result)
        except Exception as exc:
            await self.trace.append_step(iteration, call, None, error=str(exc))
            return self._tool_msg(call, {"error": str(exc)})

    def _budget_exhausted(self, iteration: int) -> AgentLoopResult:
        return AgentLoopResult(
            status="budget_exhausted",
            iterations=iteration,
            result=None,
            trace=list(self.trace.steps()),
            usage=self.budget.snapshot(),
        )
    # ... other helpers ...
```

### 22.2 Tool registry

```python
# apps/api/app/node_system/tools/registry.py
from typing import Any
from .schema import node_metadata_to_jsonschema


class ToolRegistry:
    def __init__(self, tools: list["ToolBinding"]):
        self._tools = {t.name: t for t in tools}

    def schemas(self) -> list[dict]:
        return [
            {
                "name":        t.name,
                "description": t.description,
                "input_schema": node_metadata_to_jsonschema(t.metadata),
            }
            for t in self._tools.values() if t.enabled
        ]

    async def execute(self, name: str, args: dict, ctx) -> Any:
        binding = self._tools.get(name)
        if binding is None:
            raise UnknownToolError(name)
        if not binding.within_rate_limit():
            raise ToolRateLimitedError(name)
        result = await binding.node.execute(args, ctx)
        binding.record_call()
        return result
```

### 22.3 Concurrency manager

```python
# apps/api/app/execution_engine/concurrency.py
from uuid import uuid4
import redis.asyncio as redis

RELEASE_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
"""

class ConcurrencyManager:
    def __init__(self, r: redis.Redis):
        self.r = r

    async def acquire(self, workflow_id: str, ttl_seconds: int) -> tuple[bool, str | None]:
        key = f"runmycrew:concurrency:workflow:{workflow_id}"
        token = uuid4().hex
        ok = await self.r.set(key, token, ex=ttl_seconds, nx=True)
        return bool(ok), (token if ok else None)

    async def release(self, workflow_id: str, token: str) -> bool:
        key = f"runmycrew:concurrency:workflow:{workflow_id}"
        return bool(await self.r.eval(RELEASE_SCRIPT, 1, key, token))
```

### 22.4 Stop condition

```python
# apps/api/app/node_system/nodes/ai/agent/stop_condition.py
import jsonata


def evaluate_success_when(expression: str | None, result: Any) -> bool:
    if not expression:
        return True
    try:
        return bool(jsonata.compile(expression).evaluate(result))
    except Exception:
        # invalid expression treated as no condition; logged + flagged at save time
        return True
```

---

## 23. Reviewer checklist

Before approving this doc, confirm:

- [ ] Section 19 open questions all have a tentative answer recorded
  in PR comments.
- [ ] No Phase 1 file paths conflict with existing in-flight PRs.
- [ ] Cost table in `pricing.py` covers every LLM model the existing
  `ai.agent` node supports.
- [ ] Migration scripts are confirmed forward-only + zero-downtime
  with our Alembic config.
- [ ] The naming choice (`ai.agent_loop` separate from `ai.agent`) is
  acceptable to product.
- [ ] The 5-phase rollout (15-day calendar) fits the next sprint.

Once checked, comment `LGTM` on the PR. Phase 1 PR opens the next
business day.

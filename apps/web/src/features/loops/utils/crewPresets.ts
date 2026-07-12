// Curated role-agent presets shown in the Loop Engineering palette instead of
// the raw node list. Each preset maps to a real backend node `type` and seeds
// role-specific default properties, so dropping one onto the canvas produces a
// configured crew member rather than an empty node.
//
// Resolved node types (verified against the backend node registry):
//   trigger.chat_app — Chat App    (category trigger)
//   ai.agent_crew   — Agent Crew   (category ai)
//   action.agent    — Agent        (category ai)
//   action.evaluator— Evaluator    (category ai)  — model-judge checker (ladder L4)
//   ai.verify       — Verify       (category ai)  — objective checker (ladder L1–L3)
//   logic.human_input — Human Input (category logic)
//   action.memory   — Memory       (category ai)
//
// A preset is only rendered when its `nodeType` exists in the loaded
// definitions (see useNodeLibrary), so listing one whose backend node is
// missing degrades gracefully.

export interface CrewPreset {
  id: string
  label: string
  description: string
  icon: string
  color: string
  nodeType: string
  defaultProperties: Record<string, unknown>
}

export const CREW_PRESETS: CrewPreset[] = [
  {
    id: 'chat-app',
    label: 'Chat App',
    description: 'Hosted chat entry point',
    icon: 'MessagesSquare',
    color: '#8b5cf6',
    nodeType: 'trigger.chat_app',
    // Node defaults (title, mode, rate limits…) come from the backend
    // properties model — nothing crew-specific to seed here.
    defaultProperties: {},
  },
  {
    id: 'crew',
    label: 'Crew',
    description: 'Orchestrates the loop',
    icon: 'Users',
    color: '#7c3aed',
    nodeType: 'ai.agent_crew',
    defaultProperties: { goal: '', maxRounds: 4 },
  },
  {
    id: 'planner',
    label: 'Planner',
    description: 'Plans · writes the spec',
    icon: 'ClipboardList',
    color: '#2563eb',
    nodeType: 'action.agent',
    defaultProperties: {
      messages: [
        {
          role: 'system',
          content:
            'You are the planner. Turn the goal into a concrete, buildable spec. On a reviewer rejection, revise the weakest part — not everything.',
        },
        { role: 'user', content: '{{$trigger}}' },
      ],
      temperature: 0.3,
    },
  },
  {
    id: 'worker',
    label: 'Worker',
    description: 'Builds from the spec',
    icon: 'Hammer',
    color: '#0891b2',
    nodeType: 'action.agent',
    defaultProperties: {
      messages: [
        {
          role: 'system',
          content:
            'Build exactly what the spec says. One change per round. Leave working code untouched.',
        },
        { role: 'user', content: '{{$json}}' },
      ],
      temperature: 0.2,
    },
  },
  {
    id: 'verify',
    label: 'Verify',
    description: 'Objective check · L1–L3',
    icon: 'ShieldCheck',
    color: '#3fb98b',
    nodeType: 'ai.verify',
    // Defaults to an L1 deterministic assertion — the strongest, most
    // autonomous rung. Edit the expression, or switch mode to rule (L2) /
    // http · code (L3) in the inspector. Unlike the model-judge Reviewer,
    // this produces a reproducible pass/fail, not an opinion.
    defaultProperties: {
      mode: 'expression',
      expression: '{{$step.passed}} == true',
    },
  },
  {
    id: 'reviewer',
    label: 'Reviewer',
    description: 'Model judge · L4',
    icon: 'CheckCheck',
    color: '#16a34a',
    nodeType: 'action.evaluator',
    defaultProperties: {
      provider: 'openai',
      content: '{{$step.content}}',
      metrics: [
        { name: 'correctness', description: 'Does it meet the spec and actually work?', min: 0, max: 10 },
        { name: 'completeness', description: 'Is anything missing?', min: 0, max: 10 },
      ],
    },
  },
  {
    id: 'task-planner',
    label: 'Task Planner',
    description: 'Decomposes a goal into a task DAG',
    icon: 'ListChecks',
    color: '#0ea5e9',
    nodeType: 'ai.task_planner',
    defaultProperties: {
      goal: '{{$trigger.goal}}',
      available_roles: ['researcher', 'writer', 'reviewer'],
      max_tasks: 6,
    },
  },
  {
    id: 'parallel-agents',
    label: 'Parallel Agents',
    description: 'Fan-out one agent per task',
    icon: 'GitBranch',
    color: '#10b981',
    nodeType: 'ai.parallel',
    defaultProperties: {
      tasks_input: '={{$previous_node.output.tasks}}',
      persona_map: {},
      max_concurrent: 4,
    },
  },
  {
    id: 'human-approval',
    label: 'Human Approval',
    description: 'Gate irreversible steps',
    icon: 'UserCheck',
    color: '#d97706',
    nodeType: 'logic.human_input',
    defaultProperties: {},
  },
  {
    id: 'memory',
    label: 'Memory',
    description: 'State across rounds',
    icon: 'Database',
    color: '#64748b',
    nodeType: 'action.memory',
    defaultProperties: {},
  },
]

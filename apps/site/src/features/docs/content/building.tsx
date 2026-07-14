import Link from 'next/link'
import type { DocContent } from './index'

/**
 * Building-workflows group. Node types, trigger kinds, logic nodes, model
 * providers and the Copilot generator all mirror the backend node registry
 * (apps/api/app/node_system) and copilot engine.
 */
export const BUILDING: Record<string, DocContent> = {
  'crew-ai': {
    toc: [
      { id: 'what', label: 'What Crew AI does' },
      { id: 'how', label: 'How generation works' },
      { id: 'agents', label: 'Agent nodes' },
      { id: 'personas', label: 'Personas' },
      { id: 'models', label: 'Models & providers' },
      { id: 'edit', label: 'Editing with AI' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Building workflows
        </p>
        <h1>Crew AI</h1>
        <p className="lead">
          Describe an automation in plain English and Crew AI builds the
          graph — choosing the trigger, wiring conditions, and placing the
          right action for every connected app.
        </p>

        <h2 id="what">What Crew AI does</h2>
        <p>
          Crew AI (the <em>Copilot</em>) turns a sentence into a working
          workflow. It doesn’t generate a black box — it emits real nodes and
          edges you can inspect, tweak and run, the same graph the engine
          executes.
        </p>

        <h2 id="how">How generation works</h2>
        <p>
          The Copilot runs an agentic loop (up to 10 iterations) that streams
          atomic graph operations — <code>add_node</code>, <code>add_edge</code>{' '}
          — to the editor over SSE, so you watch the workflow assemble node by
          node. Under the hood it uses two tools to stay grounded in the real
          catalog:
        </p>
        <ul>
          <li><code>search_node_types</code> — find the right node for a task across 340+ types.</li>
          <li><code>get_node_metadata</code> — read a node’s exact properties before configuring it.</li>
        </ul>
        <p>The result is validated and auto-laid-out before it lands in the editor.</p>

        <h2 id="agents">Agent nodes</h2>
        <p>
          Beyond deterministic steps, workflows can contain <strong>agent</strong>{' '}
          nodes that reason and call tools:
        </p>
        <ul>
          <li><code>action.agent</code> — an AI agent with a model, tools, memory and structured output.</li>
          <li><code>action.llm</code> — a single prompt → text, no tool loop.</li>
          <li><code>ai.agent_crew</code> — a maker/checker crew that verifies its own work.</li>
          <li><code>ai.task_planner</code> + <code>ai.parallel</code> — decompose a goal into a task DAG and run role-agents in parallel.</li>
          <li><code>action.knowledge</code>, <code>action.memory</code> — semantic search over your knowledge bases and run memory.</li>
        </ul>

        <h2 id="personas">Personas</h2>
        <p>
          A <strong>persona</strong> is a reusable named agent — a role, a
          prompt, and default model + tools — that you overlay onto agent nodes.
          Define “Support Triager” once and drop it into any crew.
        </p>

        <h2 id="models">Models &amp; providers</h2>
        <p>
          Route each agent to any of ten providers — OpenAI, Anthropic, Google,
          Groq, DeepSeek, Fireworks, Mistral, xAI, Together and OpenRouter — by
          adding that provider’s key. The Copilot itself defaults to a fast
          model per provider (e.g. <code>gpt-4o-mini</code>,{' '}
          <code>claude-haiku-4-5</code>, <code>gemini-2.5-flash</code>).
        </p>

        <h2 id="edit">Editing with AI</h2>
        <p>
          Crew AI also edits existing graphs — “add a Slack approval before the
          deploy step” — applying incremental changes rather than regenerating
          from scratch. For autonomous, scheduled agents, see{' '}
          <Link href="/docs/agent-loops">Agent loops</Link>.
        </p>
      </>
    ),
  },

  triggers: {
    toc: [
      { id: 'what', label: 'What a trigger is' },
      { id: 'builtin', label: 'Built-in triggers' },
      { id: 'app', label: 'App-event triggers' },
      { id: 'delivery', label: 'Webhook vs polling' },
      { id: 'test', label: 'Testing triggers' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Building workflows
        </p>
        <h1>Triggers</h1>
        <p className="lead">
          A trigger is the one node that starts a workflow. Everything
          downstream runs in response to it, with the trigger’s payload as the
          run’s first input.
        </p>

        <h2 id="what">What a trigger is</h2>
        <p>
          Each workflow has exactly one trigger. Its output — the event that
          fired it — is available to every later node as{' '}
          <code>&#123;&#123;trigger.…&#125;&#125;</code>.
        </p>

        <h2 id="builtin">Built-in triggers</h2>
        <ul>
          <li><code>trigger.manual</code> — run on demand from the editor or API.</li>
          <li><code>trigger.form</code> — collect input fields, filled at run time.</li>
          <li><code>trigger.cron</code> — run on a cron schedule (see <Link href="/docs/scheduling">Scheduling</Link>).</li>
          <li><code>trigger.webhook</code> — fire on an inbound HTTP POST (see <Link href="/docs/webhooks">Webhooks</Link>).</li>
          <li><code>trigger.chat_app</code> — publish the workflow as a hosted chat/form app.</li>
        </ul>

        <h2 id="app">App-event triggers</h2>
        <p>
          Dozens of integrations expose native event triggers — start a workflow
          on a GitHub push, a new Gmail message, a Stripe charge, a Notion page
          change, a Linear issue update, a Typeform submission, a WhatsApp
          message, and more.
        </p>

        <h2 id="delivery">Webhook vs polling</h2>
        <p>Two delivery mechanisms, chosen per trigger:</p>
        <ul>
          <li><strong>Webhook-delivered</strong> — the app pushes events to RunMyCrew instantly (GitHub, Slack, Stripe, Linear, Meta, Twilio…).</li>
          <li><strong>Polling</strong> — RunMyCrew checks the app on an interval for apps without webhooks (Gmail, Calendar, Drive, Sheets, IMAP, RSS, HubSpot, Salesforce, Asana…).</li>
        </ul>

        <h2 id="test">Testing triggers</h2>
        <p>
          Click <em>Listen</em> on a trigger to capture the next real event as a
          fixture, then build the rest of the workflow against a concrete
          payload. Validate cron expressions and preview upcoming fire times
          right in the inspector.
        </p>
      </>
    ),
  },

  conditions: {
    toc: [
      { id: 'what', label: 'Branching & filtering' },
      { id: 'nodes', label: 'Logic nodes' },
      { id: 'expr', label: 'Expressions' },
      { id: 'loops', label: 'Loops' },
      { id: 'human', label: 'Human approval' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Building workflows
        </p>
        <h1>Conditions</h1>
        <p className="lead">
          Branch, filter, loop and reshape data without writing glue code.
          Logic nodes give a workflow control flow.
        </p>

        <h2 id="what">Branching &amp; filtering</h2>
        <p>
          A condition node evaluates an expression against the run’s data and
          routes execution accordingly — continue, stop, or take a different
          path.
        </p>

        <h2 id="nodes">Logic nodes</h2>
        <ul>
          <li><code>logic.condition</code> — boolean branch (if / else).</li>
          <li><code>logic.switch</code> — route to N labeled branches by a field value.</li>
          <li><code>logic.merge</code> — join multiple branches back into one object.</li>
          <li><code>logic.set_variable</code> — stash a value for downstream nodes.</li>
          <li><code>logic.json_transform</code> — reshape or extract fields with a template.</li>
          <li><code>logic.code</code> — run Python or JavaScript for anything declarative nodes can’t express.</li>
          <li><code>logic.sub_workflow</code> — call another workflow and use its output.</li>
        </ul>

        <h2 id="expr">Expressions</h2>
        <p>
          Conditions and transforms use expression syntax (JSONata / Jinja2)
          over the run’s data. Reference upstream outputs the same way you do
          elsewhere:
        </p>
        <pre>
          <code>{`{{trigger.label}} = "urgent" and {{trigger.assignee}} is empty`}</code>
        </pre>

        <h2 id="loops">Loops</h2>
        <p>Iterate over data or repeat steps:</p>
        <ul>
          <li><code>logic.foreach</code> — run downstream nodes once per array item.</li>
          <li><code>logic.for</code> — a fixed number of iterations with a counter.</li>
          <li><code>logic.while</code> / <code>logic.do_while</code> — repeat while a condition holds.</li>
        </ul>

        <h2 id="human">Human approval</h2>
        <p>
          <code>logic.human_input</code> pauses a run and waits for a person to
          approve or supply input. The run resumes via a one-time token — see
          the <Link href="/docs/api/runs">Runs API</Link> resume endpoint.
        </p>
      </>
    ),
  },

  actions: {
    toc: [
      { id: 'what', label: 'What actions do' },
      { id: 'integrations', label: '200+ integrations' },
      { id: 'http', label: 'HTTP & databases' },
      { id: 'ai', label: 'AI actions' },
      { id: 'utility', label: 'Files & timing' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Building workflows
        </p>
        <h1>Actions</h1>
        <p className="lead">
          Actions are the nodes that <em>do</em> something — post a message,
          create an issue, query a database, call a model. A single run can fan
          out across every connected tool.
        </p>

        <h2 id="what">What actions do</h2>
        <p>
          An action takes data from upstream nodes, performs an operation
          (usually against a <Link href="/docs/oauth">connection</Link>), and
          returns a result for downstream nodes to use.
        </p>

        <h2 id="integrations">200+ integrations</h2>
        <p>
          RunMyCrew ships 200+ app integrations — Slack, GitHub, Notion, Google
          Workspace, Stripe, Salesforce, Airtable, HubSpot, Linear, Twilio,
          Shopify and many more — each with native actions for its common
          operations. No wrapper code, no maintaining API clients.
        </p>

        <h2 id="http">HTTP &amp; databases</h2>
        <ul>
          <li><code>action.http_request</code> — call any REST/GraphQL API (see <Link href="/docs/custom-apps">Custom apps</Link>).</li>
          <li><code>action.postgres</code>, <code>action.mysql</code>, <code>action.mongodb</code>, <code>action.dynamodb</code>, <code>action.neo4j</code> — query or mutate a database directly.</li>
        </ul>

        <h2 id="ai">AI actions</h2>
        <p>
          Drop intelligence into any step: summarize with <code>action.llm</code>,
          run a tool-using <code>action.agent</code>, score with{' '}
          <code>action.evaluator</code>, or generate images, speech and
          embeddings (<code>action.image_gen</code>, <code>action.tts</code>,{' '}
          <code>action.embeddings</code>). See <Link href="/docs/crew-ai">Crew AI</Link>.
        </p>

        <h2 id="utility">Files &amp; timing</h2>
        <ul>
          <li><code>common.file</code> — read a URL, write a per-run file, or parse JSON/CSV/text.</li>
          <li><code>action.delay</code> / <code>action.wait</code> — pause between steps.</li>
        </ul>
      </>
    ),
  },

  templates: {
    toc: [
      { id: 'what', label: 'Starter templates' },
      { id: 'use', label: 'Using a template' },
      { id: 'examples', label: 'Examples' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Building workflows
        </p>
        <h1>Templates</h1>
        <p className="lead">
          Templates are pre-built workflows you can copy and adapt — the
          fastest way from idea to running automation.
        </p>

        <h2 id="what">Starter templates</h2>
        <p>
          Browse <strong>Templates</strong> in the sidebar. Each is a complete
          graph with the trigger, conditions and actions already wired — you
          just connect the apps and adjust the details.
        </p>

        <h2 id="use">Using a template</h2>
        <ol>
          <li>Open a template and read what it does.</li>
          <li>Click <em>Use template</em> to copy it into your workspace.</li>
          <li>Connect any apps it needs, tweak the config, and run.</li>
        </ol>

        <h2 id="examples">Examples</h2>
        <ul>
          <li><strong>Urgent issues → Slack</strong> — label-triggered incident routing + a Linear ticket.</li>
          <li><strong>Daily standup digest</strong> — summarize GitHub activity with AI and post to Slack on a schedule.</li>
          <li><strong>New lead → CRM</strong> — a Meta lead form to Notion plus a welcome email.</li>
          <li><strong>Agent loops</strong> — Triage bugs, auto-merge Dependabot PRs, Sentry → GitHub (see <Link href="/docs/agent-loops">Agent loops</Link>).</li>
        </ul>
      </>
    ),
  },
}

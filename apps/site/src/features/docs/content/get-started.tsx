import Link from 'next/link'
import type { DocContent } from './index'

/** Get-started group — quickstart, core concepts, glossary. */
export const GET_STARTED: Record<string, DocContent> = {
  quickstart: {
    toc: [
      { id: 'connect', label: '1. Connect an app' },
      { id: 'describe', label: '2. Describe the workflow' },
      { id: 'review', label: '3. Review the graph' },
      { id: 'run', label: '4. Run it' },
      { id: 'observe', label: '5. Observe' },
      { id: 'next', label: 'Next steps' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Get started
        </p>
        <h1>Quickstart</h1>
        <p className="lead">
          Build and run your first workflow in under five minutes. We’ll wire a
          GitHub issue to a Slack message — no code.
        </p>

        <h2 id="connect">1. Connect an app</h2>
        <p>
          From the dashboard, click <em>Connect app</em> and authorize{' '}
          <strong>GitHub</strong> and <strong>Slack</strong>. Each opens an
          OAuth consent screen and returns to RunMyCrew marked{' '}
          <strong>OK</strong>. See <Link href="/docs/oauth">OAuth integrations</Link>.
        </p>

        <h2 id="describe">2. Describe the workflow</h2>
        <p>
          In the <strong>Build with AI</strong> box, type what you want in plain
          English:
        </p>
        <blockquote>
          When a GitHub issue is labeled “urgent”, post it to #incidents in
          Slack and create a Linear ticket.
        </blockquote>
        <p>
          Press <em>Generate</em>. Crew AI maps your sentence to a trigger, a
          condition and two actions. Read more in{' '}
          <Link href="/docs/crew-ai">Crew AI</Link>.
        </p>

        <h2 id="review">3. Review the graph</h2>
        <p>
          The editor opens with the generated graph. Every node is editable —
          click one to open the inspector, change a channel, add a filter, or
          wire an extra step. Nothing runs until you say so.
        </p>

        <h2 id="run">4. Run it</h2>
        <p>
          Click <strong>Run</strong> to execute once with a sample payload, or{' '}
          <strong>Activate</strong> to arm the trigger so it fires on real
          events. You can also trigger a run from the API:
        </p>
        <pre>
          <code>{`POST /api/v1/workflows/{workflow_id}/run
Authorization: Bearer fuse_live_…`}</code>
        </pre>

        <h2 id="observe">5. Observe</h2>
        <p>
          Open the run in <strong>Runs</strong>. Every step shows its input,
          output, timing and status. If something failed, you’ll see exactly
          which node and why — then <Link href="/docs/replay">replay</Link> it
          with the same payload after a fix.
        </p>

        <h2 id="next">Next steps</h2>
        <ul>
          <li><Link href="/docs/concepts">Core concepts</Link> — how workflows execute.</li>
          <li><Link href="/docs/triggers">Triggers</Link>, <Link href="/docs/conditions">conditions</Link>, <Link href="/docs/actions">actions</Link>.</li>
          <li><Link href="/docs/agent-loops">Agent loops</Link> — autonomous, scheduled agents.</li>
        </ul>
      </>
    ),
  },

  concepts: {
    toc: [
      { id: 'workflow', label: 'Workflows are graphs' },
      { id: 'nodes', label: 'Nodes' },
      { id: 'data', label: 'How data flows' },
      { id: 'runs', label: 'Runs & the engine' },
      { id: 'kinds', label: 'Automations vs crews' },
      { id: 'versions', label: 'Versions' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Get started
        </p>
        <h1>Core concepts</h1>
        <p className="lead">
          Five ideas explain almost everything in RunMyCrew: workflows, nodes,
          data flow, runs, and connections.
        </p>

        <h2 id="workflow">Workflows are graphs</h2>
        <p>
          A <strong>workflow</strong> is a directed graph of{' '}
          <code>&#123; nodes, edges &#125;</code>. A <em>trigger</em> node
          starts it; edges carry execution from one node to the next; leaf
          nodes end the run. The graph is the single source of truth — the same
          shape you see in the editor is what the engine executes and what the
          API returns.
        </p>

        <h2 id="nodes">Nodes</h2>
        <p>Every node is one of a few kinds:</p>
        <ul>
          <li><strong>Trigger</strong> — starts the workflow (schedule, webhook, app event, or manual). One per workflow.</li>
          <li><strong>Condition</strong> — branches or filters the run based on data.</li>
          <li><strong>Action</strong> — does something in a connected app (post a message, create an issue, send an email).</li>
          <li><strong>AI / agent</strong> — calls a model to summarize, classify, or autonomously drive tools.</li>
          <li><strong>HTTP</strong> — calls any REST/GraphQL API directly.</li>
        </ul>
        <p>
          See <Link href="/docs/triggers">Triggers</Link>,{' '}
          <Link href="/docs/conditions">Conditions</Link> and{' '}
          <Link href="/docs/actions">Actions</Link> for each in depth.
        </p>

        <h2 id="data">How data flows</h2>
        <p>
          Each node produces a JSON output. Downstream nodes reference upstream
          outputs with a template expression — for example{' '}
          <code>&#123;&#123;trigger.issue.title&#125;&#125;</code> or{' '}
          <code>&#123;&#123;steps.summarize.text&#125;&#125;</code>. Secrets are
          referenced the same way via{' '}
          <code>&#123;&#123;secrets.NAME&#125;&#125;</code> and injected only at
          run time.
        </p>

        <h2 id="runs">Runs &amp; the engine</h2>
        <p>
          Each execution is a <strong>run</strong> with a status (
          <code>running</code>, <code>success</code>, <code>failed</code>,{' '}
          <code>cancelled</code>), the input that started it, the output it
          produced, and a per-node log. Runs execute on background workers, so a
          slow action never blocks the trigger. Failed steps follow the
          workflow’s <Link href="/docs/retries">retry policy</Link>.
        </p>

        <h2 id="kinds">Automations vs crews</h2>
        <p>
          A workflow’s <code>kind</code> is <strong>automation</strong>{' '}
          (deterministic trigger → steps) or <strong>crew</strong> (an
          AI-driven agent workflow). Both share the same graph model, editor and
          run history. Autonomous, scheduled crews are covered in{' '}
          <Link href="/docs/agent-loops">Agent loops</Link>.
        </p>

        <h2 id="versions">Versions</h2>
        <p>
          Editing a workflow’s graph auto-snapshots the previous version. Browse
          history and roll back at any time — see the{' '}
          <Link href="/docs/api/workflows">Workflows API</Link>.
        </p>
      </>
    ),
  },

  glossary: {
    toc: [{ id: 'terms', label: 'Terms' }],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Get started
        </p>
        <h1>Glossary</h1>
        <p className="lead">The vocabulary used across RunMyCrew and these docs.</p>

        <h2 id="terms">Terms</h2>
        <ul>
          <li><strong>Workflow</strong> — a graph of nodes that automates a task.</li>
          <li><strong>Node</strong> — one step: a trigger, condition, action, AI, or HTTP call.</li>
          <li><strong>Trigger</strong> — the node that starts a workflow (schedule, webhook, event, manual).</li>
          <li><strong>Action</strong> — a node that performs work in a connected app.</li>
          <li><strong>Condition</strong> — a node that branches or filters based on data.</li>
          <li><strong>Run / execution</strong> — one invocation of a workflow, with a status and logs.</li>
          <li><strong>Connection</strong> — an OAuth-authorized link to an external app, scoped to a workspace.</li>
          <li><strong>Secret</strong> — an encrypted workspace value referenced as <code>&#123;&#123;secrets.NAME&#125;&#125;</code>.</li>
          <li><strong>Crew</strong> — an AI-driven workflow whose action is an agent with tool access.</li>
          <li><strong>Agent loop</strong> — a scheduled crew that runs autonomously under a budget.</li>
          <li><strong>Workspace</strong> — the boundary that owns workflows, connections and members.</li>
          <li><strong>Trigger drift / catch-up</strong> — how missed cron fires are handled (see <Link href="/docs/scheduling">Scheduling</Link>).</li>
          <li><strong>API key</strong> — a <code>fuse_live_</code> token for programmatic access.</li>
        </ul>
      </>
    ),
  },
}

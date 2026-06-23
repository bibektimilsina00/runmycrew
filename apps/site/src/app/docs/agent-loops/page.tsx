import Link from 'next/link'
import { MarketingNav } from '@/features/marketing'
import { DocsLayout, DocsToc, type TocEntry } from '@/features/docs'

/**
 * Dedicated agent-loops doc page — bypasses the catch-all placeholder so
 * we can ship real prose for the loop-engineering feature (Phases 1–6).
 * Keep the page-shell shape identical to the catch-all so the sidebar
 * + TOC components don’t need to change.
 */
export default function AgentLoopsPage() {
  const toc: TocEntry[] = [
    { id: 'what-is-a-loop', label: 'What is a loop?' },
    { id: 'why', label: 'Why agent loops?' },
    { id: 'anatomy', label: 'Anatomy of a loop' },
    { id: 'budgets', label: 'Budgets — the unkillable safety net' },
    { id: 'success-when', label: 'Success conditions' },
    { id: 'concurrency', label: 'Concurrency + cron drift' },
    { id: 'escalation', label: 'Escalation' },
    { id: 'trace', label: 'The live trace' },
    { id: 'templates', label: 'Starter templates' },
    { id: 'self-host', label: 'Self-hosting notes' },
  ]

  return (
    <>
      <MarketingNav />
      <DocsLayout toc={<DocsToc items={toc} />}>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Run &amp; observe
        </p>
        <h1>Agent loops</h1>
        <p className="lead">
          Schedule autonomous agents that own recurring work — triaging bugs,
          merging dependency PRs, turning Sentry alerts into GitHub issues —
          with hard budgets, escalation, and a live trace you can audit step
          by step.
        </p>

        <h2 id="what-is-a-loop">What is a loop?</h2>
        <p>
          A <strong>loop</strong> is a workflow whose trigger fires on its
          own — usually a cron expression, sometimes a webhook — and whose
          action is an agent node with tool access. Each fire is one
          autonomous run: the agent thinks, calls tools, observes results,
          and stops when its success condition holds or its budget runs out.
        </p>
        <p>
          Concretely, a loop is just three nodes wired in a row:
        </p>
        <pre>
          <code>{`trigger.cron  →  action.agent  →  (optional) success/failure branches`}</code>
        </pre>

        <h2 id="why">Why agent loops?</h2>
        <p>
          Most automation today is{' '}
          <em>brittle if-this-then-that</em> wiring — every branch is
          hard-coded, every edge case lives in a special-cased node, and any
          drift in the upstream system means a Saturday-morning page. Agent
          loops invert that:
        </p>
        <ul>
          <li>
            You describe the <em>goal</em> in one prompt: <em>“If a Linear
            bug ticket has no owner after 30 minutes in <code>Triage</code>,
            assign it to the on-call engineer and post a heads-up in
            <code> #eng-triage</code>.”</em>
          </li>
          <li>
            The agent picks its own tools, retries on its own, reasons about
            partial failures, and stops when the work is done.
          </li>
          <li>
            You set a <strong>budget</strong> so it can never run away — at
            worst it gives up and pages a human.
          </li>
        </ul>

        <h2 id="anatomy">Anatomy of a loop</h2>
        <p>
          Every loop ships with the same building blocks. They are all
          exposed in the agent node inspector under <em>Advanced</em>.
        </p>
        <ul>
          <li>
            <strong>Iterations</strong> — max reasoning turns per fire
            (default 10, hard cap 100).
          </li>
          <li>
            <strong>Wall-clock budget</strong> — max seconds the loop is
            allowed to run (default 600, hard cap 3 600).
          </li>
          <li>
            <strong>Token + cost budget</strong> — max input tokens and max
            USD spend (hard caps 5M tokens, $50 per run).
          </li>
          <li>
            <strong>Success condition</strong> — a JSONata expression
            against the agent’s final JSON output (e.g.{' '}
            <code>action_taken or no_new_issues</code>).
          </li>
          <li>
            <strong>Failure policy</strong> — what to do when no success
            condition holds: <code>retry</code>,{' '}
            <code>escalate</code>, or <code>silent</code>.
          </li>
        </ul>

        <h2 id="budgets">Budgets — the unkillable safety net</h2>
        <p>
          Loops cost real money. Every iteration is an LLM call; every tool
          call is an API hit. Without a budget the worst-case is a bug in
          your prompt costing thousands of dollars overnight.
        </p>
        <p>
          RunMyCrew enforces four budgets at the loop’s edge. The agent
          checks them before every LLM call and short-circuits with a{' '}
          <code>budget_exhausted</code> status the moment any one trips:
        </p>
        <ul>
          <li>
            <code>maxIterations</code> — counts assistant turns.
          </li>
          <li>
            <code>maxSeconds</code> — wall-clock against the run’s start
            time.
          </li>
          <li>
            <code>maxInputTokens</code> — sum of every prompt’s input
            tokens.
          </li>
          <li>
            <code>maxCostUsd</code> — sums per-model pricing across every
            LLM call.
          </li>
        </ul>
        <p>
          The system clamps each user value at the hard caps above so a
          mis-typed config can’t bypass them.
        </p>

        <h2 id="success-when">Success conditions</h2>
        <p>
          The agent’s final response is parsed as JSON when possible. The{' '}
          <code>successWhen</code> field is a JSONata expression run against
          that object. If it evaluates truthy, the loop completes. If it
          evaluates falsy (and there are iterations left), the agent gets
          one more turn with a synthesised{' '}
          <em>re-evaluate</em> message and tries again.
        </p>
        <p>
          The expression is validated at save-time so a typo fails the
          editor rather than the cron at 3 AM.
        </p>

        <h2 id="concurrency">Concurrency + cron drift</h2>
        <p>
          Cron fires don’t always land on time — workers crash, queues back
          up, deploys eat a tick. Two concerns:
        </p>
        <ol>
          <li>
            <strong>Concurrency</strong> — what happens when fire N+1 lands
            before fire N has finished?
          </li>
          <li>
            <strong>Drift</strong> — what happens when the worker wakes up
            10 minutes late and finds 5 missed fires?
          </li>
        </ol>
        <p>
          Each workflow picks a policy for both, persisted on the workflow
          itself:
        </p>
        <ul>
          <li>
            Concurrency: <code>skip</code> (default) — drop the new fire if
            the workflow is already running. <code>queue</code> — wait up
            to N seconds for the running fire to finish.{' '}
            <code>replace</code> — cancel the running fire and start fresh.
          </li>
          <li>
            Cron drift: <code>latest</code> (default) — fire once for{' '}
            <em>now</em> only. <code>catchup</code> — replay every missed
            tick (capped at 10).{' '}
            <code>skip</code> — drop the tick entirely if more than one
            interval late.
          </li>
        </ul>
        <p>
          Under the hood, concurrency uses a Redis{' '}
          <code>SETNX + Lua CAS-release</code> mutex keyed on the workflow
          id. The scheduler emits one Celery payload per fire it decides to
          honour.
        </p>

        <h2 id="escalation">Escalation</h2>
        <p>
          When <code>failurePolicy = escalate</code> and a loop ends in any
          terminal state besides success, the workspace’s{' '}
          <strong>escalation channel</strong> gets a structured payload
          with the run id, link, status, failure reason, usage totals, and
          a five-step trace summary (last tool calls). Channels supported:
        </p>
        <ul>
          <li>Slack (Block Kit message)</li>
          <li>Generic webhook (POSTs the full payload as JSON)</li>
          <li>Email (via the workspace SMTP config)</li>
        </ul>

        <h2 id="trace">The live trace</h2>
        <p>
          Open the editor’s <strong>Logs</strong> panel while a loop runs.
          Pick the agent node; a <em>Trace</em> tab appears alongside{' '}
          <em>Output</em> and <em>Input</em>. Each tool call shows up as a
          step the moment it starts, with status, arguments, result, and
          duration. The step flips from <em>running</em> to{' '}
          <em>success</em> / <em>failed</em> in place — no re-layout, no
          page refresh.
        </p>

        <h2 id="templates">Starter templates</h2>
        <p>
          Three loop templates ship in the box to copy and adapt:
        </p>
        <ul>
          <li>
            <strong>Triage Linear bugs</strong> — cron every 30 min,
            claude-sonnet-4-6, linear + slack tools.
          </li>
          <li>
            <strong>Dependabot auto-merge</strong> — webhook, claude-haiku-4-5,
            github + slack tools.
          </li>
          <li>
            <strong>Sentry → GitHub</strong> — cron every 15 min,
            gpt-5-mini, sentry + github + memory tools.
          </li>
        </ul>

        <h2 id="self-host">Self-hosting notes</h2>
        <p>
          Loops need Redis (for the concurrency mutex and the cron
          tracker) and a Celery worker running the{' '}
          <code>check_cron_triggers</code> beat. Both are part of the
          default <code>docker-compose</code> stack — see{' '}
          <Link href="/docs/self-host">Self-host overview</Link>. Set the
          escalation channel under workspace settings to route loop
          failures somewhere a human will read them.
        </p>
      </DocsLayout>
    </>
  )
}

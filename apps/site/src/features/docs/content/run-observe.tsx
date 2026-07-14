import Link from 'next/link'
import type { DocContent } from './index'

/**
 * Run & observe group. Scheduling/concurrency/drift facts mirror the cron
 * engine (also documented on the agent-loops page); retries mirror the
 * auto-injected node retry props; alerts mirror the escalation channels.
 */
export const RUN_OBSERVE: Record<string, DocContent> = {
  scheduling: {
    toc: [
      { id: 'cron', label: 'Cron triggers' },
      { id: 'validate', label: 'Validate & preview' },
      { id: 'concurrency', label: 'Concurrency' },
      { id: 'drift', label: 'Missed fires (drift)' },
      { id: 'infra', label: 'What runs the clock' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Run &amp; observe
        </p>
        <h1>Scheduling</h1>
        <p className="lead">
          Run workflows on a schedule with a cron expression — and control
          exactly what happens when fires overlap or the clock slips.
        </p>

        <h2 id="cron">Cron triggers</h2>
        <p>
          Add a <code>trigger.cron</code> node and give it a standard cron
          expression. Common patterns:
        </p>
        <pre>
          <code>{`0 9 * * 1-5     # 9:00 AM, Monday–Friday
*/15 * * * *    # every 15 minutes
0 0 1 * *       # midnight on the 1st of each month`}</code>
        </pre>

        <h2 id="validate">Validate &amp; preview</h2>
        <p>
          The inspector validates the expression as you type and previews the
          next fire times, so you never arm a broken schedule. (
          <code>POST /api/v1/cron/validate</code>,{' '}
          <code>GET /api/v1/cron/next-runs</code>.)
        </p>

        <h2 id="concurrency">Concurrency</h2>
        <p>
          What happens when the next fire lands before the previous run
          finishes? Pick a policy per workflow:
        </p>
        <ul>
          <li><code>skip</code> (default) — drop the new fire while a run is in progress.</li>
          <li><code>queue</code> — wait up to N seconds for the running fire to finish.</li>
          <li><code>replace</code> — cancel the running fire and start fresh.</li>
        </ul>
        <p>Under the hood this uses a Redis mutex keyed on the workflow id.</p>

        <h2 id="drift">Missed fires (drift)</h2>
        <p>
          Workers crash, queues back up, deploys eat a tick. When the scheduler
          wakes late and finds missed fires, the drift policy decides:
        </p>
        <ul>
          <li><code>latest</code> (default) — fire once for <em>now</em> only.</li>
          <li><code>catchup</code> — replay every missed tick (capped at 10).</li>
          <li><code>skip</code> — drop the tick if more than one interval late.</li>
        </ul>

        <h2 id="infra">What runs the clock</h2>
        <p>
          Scheduling needs the Celery <strong>beat</strong> service and Redis —
          both in the default stack. Run exactly one beat replica. See{' '}
          <Link href="/docs/self-host">Self-host overview</Link>.
        </p>
      </>
    ),
  },

  retries: {
    toc: [
      { id: 'why', label: 'Why retries' },
      { id: 'config', label: 'Per-node config' },
      { id: 'backoff', label: 'Backoff' },
      { id: 'fail', label: 'When retries run out' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Run &amp; observe
        </p>
        <h1>Retries</h1>
        <p className="lead">
          External APIs fail transiently — rate limits, timeouts, blips.
          RunMyCrew retries failed steps automatically so a hiccup doesn’t sink
          the whole run.
        </p>

        <h2 id="why">Why retries</h2>
        <p>
          Most action failures are temporary. Retrying with backoff turns a
          flaky dependency into a non-event, and keeps your alerts meaningful —
          you only hear about failures that <em>persist</em>.
        </p>

        <h2 id="config">Per-node config</h2>
        <p>
          Every node exposes retry settings in its inspector — the max attempt
          count and the delay between attempts. Defaults are sensible; raise
          them for slow or rate-limited APIs, lower them for steps that must not
          repeat.
        </p>

        <h2 id="backoff">Backoff</h2>
        <p>
          Retries wait between attempts (backoff) so you don’t hammer a
          struggling API. Each attempt is logged on the run, so you can see how
          many it took to succeed.
        </p>

        <h2 id="fail">When retries run out</h2>
        <p>
          If a step exhausts its attempts, the run is marked{' '}
          <code>failed</code> and your <Link href="/docs/alerts">alerts</Link>{' '}
          fire. Fix the cause, then <Link href="/docs/replay">replay</Link> the
          run with its original input.
        </p>
      </>
    ),
  },

  'run-history': {
    toc: [
      { id: 'list', label: 'The runs list' },
      { id: 'detail', label: 'Run detail' },
      { id: 'filter', label: 'Search & filter' },
      { id: 'api', label: 'Via the API' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Run &amp; observe
        </p>
        <h1>Run history</h1>
        <p className="lead">
          Every execution is recorded end-to-end — what triggered it, what each
          step did, how long it took, and whether it succeeded.
        </p>

        <h2 id="list">The runs list</h2>
        <p>
          <strong>Runs</strong> shows recent executions across the workspace
          with status, trigger type, duration and time. Green means success,
          amber a warning, red a failure.
        </p>

        <h2 id="detail">Run detail</h2>
        <p>
          Open any run to see the full step log — each node’s input, output,
          status and timing. Failed nodes surface the exact error inline, so
          you don’t dig through raw logs.
        </p>

        <h2 id="filter">Search &amp; filter</h2>
        <p>
          Filter by status or workflow to find the runs you care about — e.g.
          every <code>failed</code> run in the last day.
        </p>

        <h2 id="api">Via the API</h2>
        <p>
          The same data is available programmatically — list, read, rerun and
          cancel runs through the <Link href="/docs/api/runs">Runs API</Link>.
        </p>
      </>
    ),
  },

  alerts: {
    toc: [
      { id: 'what', label: 'Failure alerts' },
      { id: 'channels', label: 'Channels' },
      { id: 'payload', label: "What's in an alert" },
      { id: 'escalate', label: 'Escalation policy' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Run &amp; observe
        </p>
        <h1>Alerts</h1>
        <p className="lead">
          Know the moment something drifts. When a run fails — or an agent loop
          ends anywhere but success — RunMyCrew notifies the channel you choose.
        </p>

        <h2 id="what">Failure alerts</h2>
        <p>
          Alerts fire on terminal failure after retries are exhausted, so you
          only hear about problems that need a human. Set the workspace’s
          escalation channel under settings.
        </p>

        <h2 id="channels">Channels</h2>
        <ul>
          <li><strong>Slack</strong> — a Block Kit message to a channel.</li>
          <li><strong>Webhook</strong> — the full alert POSTed as JSON to your endpoint.</li>
          <li><strong>Email</strong> — via the workspace’s email config.</li>
        </ul>

        <h2 id="payload">What’s in an alert</h2>
        <p>
          Each alert carries the run id and link, the status and failure reason,
          usage totals, and a short trace summary of the last steps — enough to
          triage without opening the app.
        </p>

        <h2 id="escalate">Escalation policy</h2>
        <p>
          For autonomous agents you can set a failure policy of{' '}
          <code>retry</code>, <code>escalate</code> or <code>silent</code> —
          see <Link href="/docs/agent-loops">Agent loops</Link> for how budgets
          and escalation work together.
        </p>
      </>
    ),
  },

  replay: {
    toc: [
      { id: 'inspect', label: 'The run inspector' },
      { id: 'trace', label: 'The live trace' },
      { id: 'rerun', label: 'Rerun & replay' },
      { id: 'resume', label: 'Resume paused runs' },
    ],
    body: (
      <>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Run &amp; observe
        </p>
        <h1>Run replay</h1>
        <p className="lead">
          Inspect any run step by step, then re-run it with the exact same
          payload after a fix — no need to recreate the original event.
        </p>

        <h2 id="inspect">The run inspector</h2>
        <p>
          Open a run and pick a node to see its <em>Input</em>, <em>Output</em>{' '}
          and timing. This is the fastest way to understand what a workflow
          actually did versus what you expected.
        </p>

        <h2 id="trace">The live trace</h2>
        <p>
          For agent nodes, a <em>Trace</em> tab shows every tool call as it
          happens — arguments, result, duration — flipping from{' '}
          <em>running</em> to <em>success</em>/<em>failed</em> in place, no page
          refresh.
        </p>

        <h2 id="rerun">Rerun &amp; replay</h2>
        <p>
          Click <em>Rerun</em> (or <code>POST /api/v1/executions/&#123;id&#125;/rerun</code>)
          to replay the workflow with the original input. Perfect for verifying
          a fix against the exact case that failed.
        </p>

        <h2 id="resume">Resume paused runs</h2>
        <p>
          Runs paused on a <Link href="/docs/conditions">human-approval</Link>{' '}
          step resume when the approver acts — or via{' '}
          <code>POST /api/v1/executions/&#123;id&#125;/resume</code> with the
          one-time token.
        </p>
      </>
    ),
  },
}

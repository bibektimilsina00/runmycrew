import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'
import { PostVisual, findPost, POSTS } from '@/features/blog'

/**
 * Dedicated post body for the loop-engineering launch — bypasses the
 * generic [slug] placeholder so we can ship real prose. Same shell as
 * the catch-all post page, just the prose block is real instead of stub.
 */
export default function LoopEngineeringPost() {
  const post = findPost('loop-engineering')!
  const related = POSTS.filter((p) => p.slug !== post.slug).slice(0, 3)

  return (
    <>
      <MarketingNav />
      <main>
        <article>
          <section className="pt-[120px] sm:pt-[160px]">
            <Container className="max-w-[820px] px-7">
              <Link
                href="/blog"
                className="mb-7 inline-flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                <ArrowLeft className="h-[14px] w-[14px]" strokeWidth={1.9} /> Back to blog
              </Link>

              <div className="flex items-center gap-2 text-[11.5px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
                <span className="text-primary">{post.category}</span>
                <span className="text-border">·</span>
                <span>{post.date}</span>
                <span className="text-border">·</span>
                <span>{post.read}</span>
              </div>
              <h1 className="m-0 mt-4 text-balance text-[clamp(34px,4.4vw,52px)] font-[560] leading-[1.08] tracking-[-0.022em] text-foreground">
                {post.title}
              </h1>
              <p className="m-0 mt-4 text-[17px] leading-[1.55] text-muted-foreground">
                {post.excerpt}
              </p>
            </Container>
          </section>

          <section className="mt-12">
            <Container className="max-w-[1080px] px-7">
              <div className="aspect-[16/9] overflow-hidden rounded-[14px] border border-border">
                <PostVisual which={post.visual} />
              </div>
            </Container>
          </section>

          <section className="my-16">
            <Container className="max-w-[820px] px-7">
              <div className="prose-docs">
                <p className="lead">
                  Crew AI showed how one prompt can build a workflow. Loops
                  show how a workflow can run itself — over and over, on a
                  schedule or a webhook, with a budget, a success
                  condition, and a place to page a human when reality
                  drifts from the plan.
                </p>

                <h2>The problem with most “automation”</h2>
                <p>
                  Most automation is brittle if-this-then-that wiring. Every
                  branch is hard-coded, every edge case lives in its own
                  node, and any drift in the upstream system means a
                  Saturday-morning page. The deeper problem: the system has
                  no goal — only a graph. So whenever a tool returns
                  something it wasn’t told to expect, the automation
                  either silently misroutes or fails open.
                </p>
                <p>
                  We tried building a “smarter if-this-then-that” more than
                  once. It doesn’t generalise. The honest reframing was to
                  put the goal back at the centre, give the agent the tools
                  it needs, and let it decide.
                </p>

                <h2>What an agent loop is</h2>
                <p>
                  A loop is three nodes wired in a row: a trigger (cron or
                  webhook), an agent node with tools, and an optional
                  success/failure branch. Each fire is one autonomous run —
                  the agent thinks, calls tools, observes results, and
                  stops when its success condition holds or its budget runs
                  out.
                </p>
                <p>
                  The first loop we built ourselves was the obvious one: a
                  cron-triggered triager that pulls open Linear bugs older
                  than 30 minutes, assigns them to the on-call engineer,
                  and posts a heads-up in <code>#eng-triage</code>. It’s
                  five lines of prompt, two tools, and a $0.05/run cost
                  cap. It just runs.
                </p>

                <h2>Budgets are the unlock</h2>
                <p>
                  Loops aren’t novel. Letting one run for a month without
                  burning the corporate card <em>is</em>. Every loop in
                  RunMyCrew enforces four budgets at the agent’s edge,
                  checked before every LLM call:
                </p>
                <ul>
                  <li><code>maxIterations</code> — max reasoning turns.</li>
                  <li><code>maxSeconds</code> — wall-clock against the run’s start.</li>
                  <li><code>maxInputTokens</code> — sum of every prompt’s input tokens.</li>
                  <li><code>maxCostUsd</code> — per-model pricing across every LLM call.</li>
                </ul>
                <p>
                  The system clamps each user value at hard caps (100
                  iterations, 1 hour, 5M tokens, $50). The moment any one
                  trips, the loop short-circuits with a{' '}
                  <code>budget_exhausted</code> status and the configured
                  failure policy fires. The worst case is you wake up to a
                  Slack message that says <em>“loop X gave up after $0.50;
                  here’s the last tool call.”</em>
                </p>

                <h2>Stop conditions, not exit nodes</h2>
                <p>
                  The agent’s final response is parsed as JSON when
                  possible. The <code>successWhen</code> field is a JSONata
                  expression run against that object. Truthy → done.
                  Falsy → one more turn with a synthesised{' '}
                  <em>re-evaluate</em> message. The expression is validated
                  at save-time, so a typo fails the editor instead of
                  failing the cron at 3 AM.
                </p>
                <p>
                  This sounds small. In practice, it’s the difference
                  between “the loop ran 30 turns and gave up” and “the loop
                  ran 4 turns, met its goal, and stopped.”
                </p>

                <h2>Concurrency + cron drift</h2>
                <p>
                  Cron fires don’t always land on time — workers crash,
                  queues back up, deploys eat a tick. Two policies per
                  workflow, settable in the inspector:
                </p>
                <ul>
                  <li>
                    <strong>Concurrency</strong> — <code>skip</code>,{' '}
                    <code>queue</code>, or <code>replace</code> when fire
                    N+1 lands before fire N finishes.
                  </li>
                  <li>
                    <strong>Cron drift</strong> — <code>latest</code>,{' '}
                    <code>catchup</code>, or <code>skip</code> when the
                    worker wakes up late and finds missed ticks.
                  </li>
                </ul>
                <p>
                  Under the hood: a Redis{' '}
                  <code>SETNX + Lua CAS-release</code> mutex keyed on the
                  workflow id, and one Celery payload per fire the
                  scheduler decides to honour.
                </p>

                <h2>Escalation</h2>
                <p>
                  When a loop fails and the failure policy is{' '}
                  <code>escalate</code>, the workspace’s escalation channel
                  gets a structured payload: run id + link, status, failure
                  reason, usage totals, and a five-step trace summary.
                  Channels supported today: Slack (Block Kit), generic
                  webhook, and email.
                </p>

                <h2>The live trace</h2>
                <p>
                  The editor’s <strong>Logs</strong> panel grew a new tab.
                  Pick an agent node mid-run; the <em>Trace</em> tab shows
                  each tool call as a step the moment it starts, with
                  status, arguments, result, and duration. Steps update in
                  place — running flips to success/failed without
                  re-layout, without a refresh. It’s the “debugger view”
                  for agents.
                </p>

                <h2>What ships today</h2>
                <ul>
                  <li>Agent loop hardening — budgets, success conditions, failure policy.</li>
                  <li>Workflow-level concurrency mutex + cron drift policy.</li>
                  <li>Per-tool registry polish — tags, dangerous flag, rate-limit hook.</li>
                  <li>Live trace timeline in the logs panel.</li>
                  <li>Escalation to Slack / webhook / email.</li>
                  <li>Three starter loop templates — triage Linear bugs, Dependabot auto-merge, Sentry → GitHub.</li>
                </ul>

                <h2>How to try it</h2>
                <p>
                  Open the workflow editor, drop a Cron trigger and an
                  Agent node, set a <code>maxCostUsd</code>, write a one-
                  sentence prompt, pick a couple of tools, and hit Run. Or
                  start from one of the bundled templates — they’re a good
                  shape for whatever your version of recurring grunt work
                  looks like.
                </p>
                <p>
                  Full design notes:{' '}
                  <Link href="/docs/agent-loops">/docs/agent-loops</Link>.
                </p>
              </div>
            </Container>
          </section>
        </article>

        <section className="border-t border-border py-16">
          <Container className="max-w-[1280px] px-7">
            <h2 className="m-0 mb-8 text-[22px] font-semibold tracking-[-0.018em] text-foreground">
              More from the blog
            </h2>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {related.map((p) => (
                <Link
                  key={p.slug}
                  href={`/blog/${p.slug}`}
                  className="group block overflow-hidden rounded-[12px] border border-border bg-card/30 transition-colors hover:border-foreground/25 hover:bg-card"
                >
                  <div className="aspect-[16/10]">
                    <PostVisual which={p.visual} />
                  </div>
                  <div className="flex flex-col gap-2 p-5">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.07em] text-primary">
                      {p.category}
                    </div>
                    <h3 className="m-0 text-[16px] font-semibold leading-snug text-foreground">
                      {p.title}
                    </h3>
                  </div>
                </Link>
              ))}
            </div>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}

import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { MarketingNav } from '@/features/marketing'
import { DocsLayout, DocsToc, type TocEntry } from '@/features/docs'

const TOC: TocEntry[] = [
  { id: 'overview',  label: 'Overview' },
  { id: 'concepts',  label: 'Core concepts' },
  { id: 'install',   label: 'Install' },
  { id: 'next',      label: 'Next steps' },
]

export default function DocsHome() {
  return (
    <>
      <MarketingNav />
      <DocsLayout toc={<DocsToc items={TOC} />}>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          Introduction
        </p>
        <h1>Welcome to Fuse</h1>
        <p className="lead">
          Fuse is the automation system for teams and agents. Connect the apps
          you already use, build workflows from a single prompt, and run
          everything with full observability.
        </p>

        <h2 id="overview">Overview</h2>
        <p>
          Workflows in Fuse are graphs of <strong>triggers</strong>,{' '}
          <strong>conditions</strong> and <strong>actions</strong>. They run
          on schedules, webhooks or app events, and every execution is logged
          end-to-end.
        </p>

        <h2 id="concepts">Core concepts</h2>
        <ul>
          <li><strong>Triggers</strong> — start a workflow from an app event, a webhook, or a schedule.</li>
          <li><strong>Conditions</strong> — branch and filter without writing glue code.</li>
          <li><strong>Actions</strong> — fan out to every connected tool in a single run.</li>
          <li><strong>Connections</strong> — OAuth-managed credentials for each integration.</li>
        </ul>

        <h2 id="install">Install</h2>
        <p>Self-host with Docker:</p>
        <pre><code>{`docker compose -f deploy/docker-compose.production.yml up -d`}</code></pre>
        <p>
          Or sign up at <a href="https://app.fuse.bibektimilsina.tech">app.fuse.bibektimilsina.tech</a>{' '}
          and skip the infra.
        </p>

        <h2 id="next">Next steps</h2>
        <div className="not-prose mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <NextCard href="/docs/quickstart" title="Quickstart" sub="Build your first workflow in 5 minutes" />
          <NextCard href="/docs/concepts"   title="Core concepts" sub="Triggers, conditions, actions" />
          <NextCard href="/docs/fuse-ai"    title="Fuse AI" sub="Generate workflows from a prompt" />
          <NextCard href="/docs/self-host"  title="Self-hosting" sub="Run on your own infra" />
        </div>
      </DocsLayout>
    </>
  )
}

function NextCard({ href, title, sub }: { href: string; title: string; sub: string }) {
  return (
    <Link
      href={href}
      className="group flex items-center justify-between gap-3 rounded-[10px] border border-border bg-card/40 px-4 py-3 transition-colors hover:border-foreground/30 hover:bg-card"
    >
      <div className="flex flex-col">
        <span className="text-[14px] font-semibold text-foreground">{title}</span>
        <span className="text-[12.5px] text-muted-foreground">{sub}</span>
      </div>
      <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" strokeWidth={1.8} />
    </Link>
  )
}

import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'
import { PricingTier, PricingComparison, TIERS } from '@/features/pricing'

const FAQ = [
  {
    q: 'Is it really free?',
    a: 'Yes. RunMyCrew is free while we’re in early access — no credit card, no trial timer, no per-run charges. Sign up and start building today.',
  },
  {
    q: 'When do paid plans arrive, and what happens to me?',
    a: 'Not for a while — and you’ll get at least 30 days’ notice before anything changes. Early users keep a generous free tier and lock in founder pricing on paid plans. Nothing gets pulled out from under you.',
  },
  {
    q: 'Do I need a credit card to start?',
    a: 'No. There’s nothing to enter and nothing to cancel. Create an account and you’re in.',
  },
  {
    q: 'Can I self-host RunMyCrew?',
    a: 'Yes — RunMyCrew ships as a Docker compose stack you can run on any VPS or Kubernetes cluster. Free to run yourself, no strings.',
  },
  {
    q: 'What counts as a run?',
    a: 'A run is a single execution of a workflow, regardless of how many steps it contains. Failed runs and retries on the same trigger fire don’t count twice.',
  },
]

export default function PricingPage() {
  return (
    <>
      <MarketingNav />
      <main>
        {/* ── Hero ────────────────────────────────────────────── */}
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[1280px] px-7 text-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-[12px] font-semibold uppercase tracking-[0.07em] text-primary">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              Early access · free
            </span>
            <h1 className="mx-auto m-0 mt-5 max-w-[860px] text-[clamp(34px,4.4vw,56px)] font-[560] leading-[1.08] tracking-[-0.022em] text-foreground text-balance">
              Free while we&rsquo;re in
              <br />
              early access
            </h1>
            <p className="mx-auto mt-5 max-w-[620px] text-[15px] leading-[1.55] text-muted-foreground">
              Every feature is unlocked and free right now — no credit card, no
              trial timer, no per-run charges. Paid plans come later, and early
              users keep a generous free tier plus founder pricing.
            </p>
          </Container>
        </section>

        {/* ── Reassurance banner ──────────────────────────────── */}
        <section className="pb-14">
          <Container className="max-w-[820px] px-7">
            <div className="grid grid-cols-1 gap-4 rounded-[14px] border border-border bg-card/30 p-6 sm:grid-cols-3">
              {[
                ['No credit card', 'Sign up and build. Nothing to enter, nothing to cancel.'],
                ['No surprise bill', 'You’re never charged during early access. Ever.'],
                ['30 days’ notice', 'Before any pricing lands — with founder rates for early users.'],
              ].map(([title, body]) => (
                <div key={title} className="flex flex-col gap-1">
                  <div className="text-[13.5px] font-semibold text-foreground">
                    {title}
                  </div>
                  <p className="m-0 text-[12.5px] leading-[1.5] text-muted-foreground">
                    {body}
                  </p>
                </div>
              ))}
            </div>
          </Container>
        </section>

        {/* ── Tiers ───────────────────────────────────────────── */}
        <section className="pb-20">
          <Container className="max-w-[1280px] px-7">
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
              {TIERS.map((t) => (
                <PricingTier key={t.slug} tier={t} />
              ))}
            </div>
          </Container>
        </section>

        {/* ── Comparison ──────────────────────────────────────── */}
        <section className="pb-20">
          <Container className="max-w-[1280px] px-7">
            <p className="mx-auto mb-6 max-w-[640px] text-center text-[13px] leading-[1.55] text-muted-foreground">
              Here&rsquo;s where plans are headed. During early access every row
              is unlocked for everyone — this is just the shape of things later.
            </p>
            <PricingComparison />
          </Container>
        </section>

        {/* ── FAQ ─────────────────────────────────────────────── */}
        <section className="pb-24">
          <Container className="max-w-[820px] px-7">
            <h2 className="m-0 mb-8 text-[clamp(24px,2.6vw,32px)] font-[560] tracking-[-0.018em] text-foreground">
              Frequently asked questions
            </h2>
            <div className="flex flex-col divide-y divide-border border-y border-border">
              {FAQ.map((item) => (
                <div key={item.q} className="py-5">
                  <div className="mb-2 text-[15px] font-semibold text-foreground">
                    {item.q}
                  </div>
                  <p className="m-0 text-[14px] leading-[1.55] text-muted-foreground">
                    {item.a}
                  </p>
                </div>
              ))}
            </div>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}

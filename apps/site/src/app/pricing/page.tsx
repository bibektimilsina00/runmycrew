import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'
import { PricingTier, PricingComparison, TIERS } from '@/features/pricing'

const FAQ = [
  {
    q: 'What counts as a run?',
    a: 'A run is a single execution of a workflow, regardless of how many steps it contains. Failed runs and retries on the same trigger fire don’t count twice.',
  },
  {
    q: 'Can I self-host Fuse?',
    a: 'Yes — Fuse ships as a Docker compose stack you can run on any VPS or Kubernetes cluster. The Enterprise plan adds VPC isolation + region pinning.',
  },
  {
    q: 'Do you charge per integration?',
    a: 'No. Every integration is included in every plan. You only pay for seats and runs.',
  },
  {
    q: 'Can I switch plans later?',
    a: 'Anytime, in both directions. Prorated automatically — you won’t pay twice for the same period.',
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
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Pricing
            </p>
            <h1 className="mx-auto m-0 mt-3 max-w-[860px] text-[clamp(34px,4.4vw,56px)] font-[560] leading-[1.08] tracking-[-0.022em] text-foreground text-balance">
              Simple pricing that scales
              <br />
              with your team
            </h1>
            <p className="mx-auto mt-5 max-w-[600px] text-[15px] leading-[1.55] text-muted-foreground">
              Start free for personal projects. Upgrade when you need more runs,
              seats or compliance features. Cancel anytime.
            </p>
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

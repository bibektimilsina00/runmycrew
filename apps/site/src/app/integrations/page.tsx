import Link from 'next/link'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'
import { IntegrationsGrid, INTEGRATIONS } from '@/features/integrations'
import { EXTERNAL_LINKS } from '@/shared/constants/routes'

export default function IntegrationsPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[1280px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Integrations
            </p>
            <h1 className="m-0 mt-3 text-[clamp(34px,4.4vw,56px)] font-[560] leading-[1.08] tracking-[-0.022em] text-foreground">
              Connect every app
              <br />
              you already use
            </h1>
            <p className="mt-5 max-w-[600px] text-[15px] leading-[1.55] text-muted-foreground">
              {INTEGRATIONS.length}+ first-party integrations across communication,
              developer tools, productivity, marketing and AI. No API keys to babysit —
              Fuse handles OAuth, token refresh and health.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-2.5">
              <Link
                href={EXTERNAL_LINKS.REGISTER}
                className="inline-flex h-[34px] items-center gap-[7px] rounded-[8px] bg-primary px-[16px] text-[13px] font-semibold text-primary-foreground transition-[filter] hover:brightness-110"
              >
                Get started
              </Link>
              <Link
                href="/docs/oauth"
                className="inline-flex h-[34px] items-center gap-[7px] rounded-[8px] border border-border bg-white/[0.02] px-[16px] text-[13px] font-medium text-foreground/90 transition-colors hover:bg-white/[0.06]"
              >
                Read the docs
              </Link>
            </div>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[1280px] px-7">
            <IntegrationsGrid />
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}

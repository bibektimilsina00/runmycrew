import Link from 'next/link'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'
import { TemplatesGrid, fetchPublicTemplates } from '@/features/templates'
import { EXTERNAL_LINKS } from '@/shared/constants/routes'

export default async function TemplatesPage() {
  const templates = await fetchPublicTemplates()
  const countCopy =
    templates.length === 0
      ? 'Curated workflows across sales, marketing, engineering and ops.'
      : `${templates.length} curated workflow${templates.length === 1 ? '' : 's'} across sales, marketing, engineering and ops.`

  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[1280px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Templates
            </p>
            <h1 className="m-0 mt-3 text-[clamp(34px,4.4vw,56px)] font-[560] leading-[1.08] tracking-[-0.022em] text-foreground">
              Start with a recipe,
              <br />
              ship in minutes
            </h1>
            <p className="mt-5 max-w-[600px] text-[15px] leading-[1.55] text-muted-foreground">
              {countCopy} Fork any template into your workspace and tailor the steps to your tools.
            </p>
            <div className="mt-7 flex flex-wrap items-center gap-2.5">
              <Link
                href={EXTERNAL_LINKS.REGISTER}
                className="inline-flex h-[34px] items-center gap-[7px] rounded-[8px] bg-primary px-[16px] text-[13px] font-semibold text-primary-foreground transition-[filter] hover:brightness-110"
              >
                Get started
              </Link>
              <Link
                href="/docs/templates"
                className="inline-flex h-[34px] items-center gap-[7px] rounded-[8px] border border-border bg-white/[0.02] px-[16px] text-[13px] font-medium text-foreground/90 transition-colors hover:bg-white/[0.06]"
              >
                Template docs
              </Link>
            </div>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[1280px] px-7">
            <TemplatesGrid templates={templates} />
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}

import Link from 'next/link'
import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import { EXTERNAL_LINKS } from '@/shared/constants/routes'

/**
 * Centered closing CTA — oversized two-line headline plus a Get-started /
 * Contact-sales pair. The pair uses opposing visual weight (light pill +
 * subtle pill) to make the primary action unambiguous.
 */
export function FinalCTA() {
  return (
    <section className="relative px-7 pb-[140px] pt-[160px] text-center">
      <Container className="max-w-[1280px] px-0">
        <Reveal y={28}>
          <h2 className="m-0 text-[clamp(36px,4.2vw,56px)] font-[590] leading-[1.1] tracking-[-0.022em] text-foreground text-balance">
            Built for the future.
            <br />
            Available today.
          </h2>
        </Reveal>
        <Reveal delay={0.15}>
          <div className="mt-11 flex items-center justify-center gap-2.5">
            <Link
              href={EXTERNAL_LINKS.REGISTER}
              className="inline-flex h-[34px] items-center gap-[7px] rounded-[8px] bg-primary px-[16px] text-[13px] font-semibold text-primary-foreground transition-[filter] hover:brightness-110"
            >
              Get started
            </Link>
            <Link
              href="/contact"
              className="inline-flex h-[34px] items-center gap-[7px] rounded-[8px] border border-border bg-white/[0.02] px-[16px] text-[13px] font-medium text-foreground/90 transition-colors hover:bg-white/[0.06]"
            >
              Contact sales
            </Link>
          </div>
        </Reveal>
      </Container>
    </section>
  )
}

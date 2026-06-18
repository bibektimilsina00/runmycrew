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
      {/* Accent halo behind the closing headline */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-[40px] -z-10 h-[480px] bg-[radial-gradient(ellipse_50%_60%_at_50%_50%,color-mix(in_oklab,var(--primary)_18%,transparent),transparent_70%)]"
      />
      <Container className="max-w-[1280px] px-0">
        <Reveal y={28}>
          <h2 className="m-0 text-[clamp(36px,4.2vw,56px)] font-[590] leading-[1.1] tracking-[-0.022em] text-foreground text-balance">
            Built for the future.
            <br />
            Available today.
          </h2>
        </Reveal>
        <Reveal delay={0.15}>
          <div className="mt-11 flex items-center justify-center gap-3">
            <Link
              href={EXTERNAL_LINKS.REGISTER}
              className="inline-flex items-center rounded-md bg-foreground px-[18px] py-[10px] text-[14px] font-medium text-background transition-[filter] hover:brightness-110"
            >
              Get started
            </Link>
            <Link
              href="#contact"
              className="inline-flex items-center rounded-md border border-border bg-white/[0.02] px-[18px] py-[10px] text-[14px] font-medium text-foreground/90 transition-colors hover:bg-white/[0.06]"
            >
              Contact sales
            </Link>
          </div>
        </Reveal>
      </Container>
    </section>
  )
}

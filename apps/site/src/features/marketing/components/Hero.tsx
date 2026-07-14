import Link from 'next/link'
import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import { EXTERNAL_LINKS } from '@/shared/constants/routes'
import { HERO } from '../data/site'
import { DashboardMockup } from './DashboardMockup'

/**
 * Landing hero. Huge editorial headline + supporting copy + a release
 * pointer in the right gutter, followed by the live dashboard product
 * shot. Padding mirrors the design (132px top, 0 below the mockup).
 */
export function Hero() {
  return (
    <section className="relative overflow-x-clip pt-[104px] sm:pt-[136px]">
      <Container className="relative max-w-[1330px] px-7">
        <Reveal y={24} delay={0.05}>
          <h1 className="m-0 max-w-[1024px] text-[clamp(34px,4.4vw,56px)] font-[560] leading-[1.08] tracking-[-0.022em] text-foreground">
            The automation
            <br />
            system for teams and agents
          </h1>
        </Reveal>
        <Reveal delay={0.1}>
          <p className="mt-6 max-w-[560px] text-[16px] font-normal leading-[1.55] tracking-normal text-muted-foreground">
            {HERO.subtitle}
          </p>
        </Reveal>

        <Reveal delay={0.15}>
          <div className="mt-8 flex flex-wrap items-center gap-2.5">
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
              Get demo
            </Link>
          </div>
        </Reveal>

        <Reveal delay={0.22} y={32}>
          <DashboardMockup />
        </Reveal>
      </Container>
    </section>
  )
}

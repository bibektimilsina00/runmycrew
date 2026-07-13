import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
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
    <section className="relative pt-[104px] sm:pt-[136px]">
      {/* Soft accent glow behind the headline — subtle, keeps the dark. */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-[80px] h-[420px] w-[820px] max-w-[92vw] -translate-x-1/2 rounded-full opacity-[0.16] blur-[120px]"
        style={{ background: 'radial-gradient(closest-side, var(--primary), transparent 72%)' }}
      />
      <Container className="relative max-w-[1330px] px-7">
        <Reveal y={20}>
          <Link
            href="#build"
            className="group mb-7 inline-flex items-center gap-2 rounded-full border border-border bg-white/[0.03] py-1 pl-1 pr-3 text-[13px] transition-colors hover:bg-white/[0.06]"
          >
            <span className="inline-flex items-center rounded-full bg-primary/15 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-primary">
              {HERO.releaseNote.label}
            </span>
            <span className="font-medium tracking-[-0.005em] text-foreground/90">
              {HERO.releaseNote.target}
            </span>
            <ArrowRight className="h-[13px] w-[13px] text-muted-foreground/70 transition-transform group-hover:translate-x-0.5" strokeWidth={1.8} />
          </Link>
        </Reveal>
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
              href="#contact"
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

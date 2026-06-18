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
    <section className="relative pt-[170px] sm:pt-[240px]">
      <Container className="max-w-[1280px] px-7">
        <Reveal y={24}>
          <h1 className="m-0 max-w-[1024px] text-[clamp(38px,5vw,64px)] font-[590] leading-[1.06] tracking-[-0.022em] text-foreground text-balance">
            {HERO.title}
          </h1>
        </Reveal>
        <Reveal delay={0.1}>
          <div className="mt-7 flex flex-wrap items-end justify-between gap-7 sm:mt-8">
            <p className="m-0 whitespace-nowrap text-[15px] font-normal leading-[1.55] tracking-normal text-muted-foreground">
              {HERO.subtitle}
            </p>
            <Link
              href="#build"
              className="group inline-flex shrink-0 items-center gap-2.5 rounded-lg px-1.5 py-1.5 transition-colors hover:bg-white/[0.04]"
            >
              <span className="text-[15px] font-medium tracking-[-0.005em] text-foreground">
                {HERO.releaseNote.label}
              </span>
              <span className="text-[15px] font-normal text-muted-foreground/85">
                {HERO.releaseNote.target}
              </span>
              <ArrowRight className="h-[15px] w-[15px] text-muted-foreground/70 transition-transform group-hover:translate-x-0.5" strokeWidth={1.8} />
            </Link>
          </div>
        </Reveal>

        <Reveal delay={0.15}>
          <div className="mt-8 flex flex-wrap items-center gap-3">
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

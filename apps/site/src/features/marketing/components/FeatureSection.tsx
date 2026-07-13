import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import type { FeatureMeta } from '../data/site'

interface Props {
  meta: FeatureMeta
  mockup: React.ReactNode
}

/**
 * Reusable shell for the four feature sections (Build / Connect / Run /
 * Observe). Owns the split heading, fig-reference link, mockup slot and
 * sublink grid. Pass the per-section meta + a mockup node — everything
 * else is shared chrome.
 */
export function FeatureSection({ meta, mockup }: Props) {
  return (
    <section id={meta.slug} className="mt-[88px] border-t border-border/80">
      <Container className="max-w-[1280px] px-7">
        <Reveal>
          <div className="grid grid-cols-1 gap-12 pt-14 lg:grid-cols-2 lg:items-start">
            <h2 className="m-0 whitespace-pre-line text-[clamp(28px,3vw,40px)] font-[590] leading-[1.125] tracking-[-0.022em] text-foreground">
              {meta.heading}
            </h2>
            <p className="m-0 text-[17px] font-normal leading-[1.6] tracking-normal text-muted-foreground">
              {meta.body}
            </p>
          </div>
        </Reveal>

        <Reveal delay={0.08}>
          <div className="mt-10 flex items-center gap-2.5">
            <span className="font-mono text-[13px] text-muted-foreground/60">
              {meta.number}
            </span>
            <Link href="#" className="text-[15px] font-semibold text-foreground/90 transition-colors hover:text-foreground">
              {meta.label}
            </Link>
            <ArrowRight className="h-[15px] w-[15px] text-muted-foreground/80" strokeWidth={1.8} />
          </div>
        </Reveal>

        <Reveal delay={0.14} y={24}>
          <div className="mt-7 transition-shadow duration-500 hover:shadow-[0_50px_120px_-50px_rgba(0,0,0,0.9),0_0_0_1px_color-mix(in_oklab,var(--primary)_25%,transparent)]">
            {mockup}
          </div>
        </Reveal>

        <div className="ml-auto mt-10 grid max-w-[620px] grid-cols-1 gap-y-2 gap-x-[60px] sm:grid-cols-2">
          {meta.sublinks.map((l, i) => (
            <Reveal key={l.n} delay={0.22 + i * 0.05}>
              <Link
                href="#"
                className="flex items-center gap-3 border-t border-white/[0.07] py-[11px] transition-opacity hover:opacity-70"
              >
                <span className="font-mono text-[12px] text-muted-foreground/60">{l.n}</span>
                <span className="text-[14.5px] font-normal text-foreground/80">{l.label}</span>
              </Link>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  )
}

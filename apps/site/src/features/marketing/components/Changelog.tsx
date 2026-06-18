import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import { CHANGELOG } from '../data/site'

/**
 * Four-up changelog grid. Each entry sits below a hairline + coloured
 * dot, the same "release marker" treatment the design uses to signal
 * timeline progression without committing to a real date axis.
 */
export function Changelog() {
  return (
    <section className="mt-[140px] border-t border-border/80">
      <Container className="max-w-[1280px] px-7">
        <Reveal>
          <h2 className="pt-14 text-[clamp(28px,3vw,40px)] font-[590] leading-[1.125] tracking-[-0.022em] text-foreground">
            Changelog
          </h2>
        </Reveal>
        <div className="mt-14 grid grid-cols-1 gap-7 sm:grid-cols-2 lg:grid-cols-4">
          {CHANGELOG.map((c, i) => (
            <Reveal key={c.title} delay={i * 0.08}>
              <div className="group">
                <div className="relative mb-6 h-3.5">
                  <div className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-white/10" />
                  <span
                    className="absolute left-0 top-1/2 h-2.5 w-2.5 -translate-y-1/2 rounded-full ring-4 ring-background transition-transform duration-500 group-hover:scale-125"
                    style={{ background: c.dot }}
                  />
                </div>
                <div className="mb-2 text-[17px] font-semibold tracking-[-0.02em] text-foreground transition-colors group-hover:text-foreground">
                  {c.title}
                </div>
                <div className="mb-3.5 text-[14px] leading-[1.55] text-muted-foreground/85">
                  {c.body}
                </div>
                <div className="font-mono text-[11px] tracking-[0.04em] text-muted-foreground/60">
                  {c.date}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
        <Link
          href="#"
          className="mt-12 inline-flex items-center gap-2 text-[15px] font-medium text-foreground/80 transition-colors hover:text-foreground"
        >
          View all
          <ArrowRight className="h-[15px] w-[15px]" strokeWidth={1.8} />
        </Link>
      </Container>
    </section>
  )
}

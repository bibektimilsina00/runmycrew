import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import { TESTIMONIALS } from '../data/site'

/**
 * Two large quote cards on contrasting brand backgrounds. Each card owns
 * its own colour palette via inline style — the design uses the cards
 * themselves as the only colourful surfaces on the page, so token
 * inheritance would just water the effect down.
 */
export function Testimonials() {
  return (
    <section className="mt-[120px]">
      <Container className="max-w-[1280px] px-7">
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {TESTIMONIALS.map((t, i) => (
            <Reveal key={t.author} delay={i * 0.1}>
            <div
              className="flex min-h-[380px] flex-col rounded-[16px] p-9 transition-transform duration-500 hover:-translate-y-1"
              style={{ background: t.bg, color: t.fg }}
            >
              <div
                className="text-[clamp(20px,1.85vw,24px)] font-medium leading-[1.35] tracking-[-0.02em] text-balance"
              >
                {t.quote}
              </div>
              <div className="mt-auto flex items-center gap-3.5 pt-7">
                <span
                  className="grid h-[42px] w-[42px] place-items-center rounded-full text-[15px] font-semibold"
                  style={{ background: t.avatarBg, color: t.avatarFg }}
                >
                  {t.initial}
                </span>
                <span className="flex flex-col leading-[1.35]">
                  <span className="text-[15px] font-semibold" style={{ color: t.fg }}>
                    {t.author}
                  </span>
                  <span className="text-[13.5px]" style={{ color: t.subFg }}>
                    {t.role}
                  </span>
                </span>
              </div>
            </div>
            </Reveal>
          ))}
        </div>

        <div className="mt-7 flex flex-wrap items-center justify-between gap-4">
          <span className="text-[16px] text-muted-foreground/85">
            Fuse runs automations for teams of every size. From solo builders to scaling startups.
          </span>
          <Link
            href="#"
            className="inline-flex items-center gap-2 text-[15px] font-medium text-foreground/80 transition-colors hover:text-foreground"
          >
            Customer stories
            <ArrowRight className="h-[15px] w-[15px]" strokeWidth={1.8} />
          </Link>
        </div>
      </Container>
    </section>
  )
}

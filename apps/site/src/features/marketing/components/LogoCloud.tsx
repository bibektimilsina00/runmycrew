import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import { LOGOS } from '../data/site'

/**
 * Text-style logo row. The design intentionally renders brand names as
 * type rather than rasterised logos — keeps the strip crisp at any size
 * and avoids licensing the marks for marketing use.
 */
export function LogoCloud() {
  return (
    <section className="pt-24">
      <Container className="max-w-[1280px] px-7">
        <div className="flex flex-wrap items-center justify-between gap-x-10 gap-y-[18px]">
          {LOGOS.map((logo, i) => (
            <Reveal key={logo} delay={i * 0.04}>
              <span className="text-[22px] font-semibold tracking-[-0.02em] text-foreground/60 transition-colors hover:text-foreground/90">
                {logo}
              </span>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  )
}

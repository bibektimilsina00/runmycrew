import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import { LOGOS } from '../data/site'

/**
 * Brand strip. Real monochrome marks (mark + wordmark) served from
 * cdn.simpleicons.org tinted to a muted foreground, brightening on hover
 * — crisp at any size, no bundled assets. A short label anchors the row
 * so it reads as a statement, not a floating list of names.
 */
export function LogoCloud() {
  return (
    <section className="pt-16 sm:pt-20">
      <Container className="max-w-[1280px] px-7">
        <Reveal>
          <p className="mb-8 font-mono text-[12px] uppercase tracking-[0.14em] text-muted-foreground/50">
            Connects the tools your team already runs on
          </p>
        </Reveal>
        <div className="flex flex-wrap items-center gap-x-12 gap-y-6 sm:gap-x-16">
          {LOGOS.map((logo, i) => (
            <Reveal key={logo.slug} delay={i * 0.04}>
              <span className="group inline-flex items-center gap-2.5">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`https://cdn.simpleicons.org/${logo.slug}/9ca3af`}
                  alt={logo.name}
                  width={20}
                  height={20}
                  loading="lazy"
                  className="h-[20px] w-[20px] opacity-70 transition-opacity group-hover:opacity-100"
                />
                <span className="text-[17px] font-medium tracking-[-0.01em] text-foreground/55 transition-colors group-hover:text-foreground/90">
                  {logo.name}
                </span>
              </span>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  )
}

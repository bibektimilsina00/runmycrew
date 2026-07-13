import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import { LOGOS } from '../data/site'

// Slack revoked its Simple Icons license (cdn.simpleicons.org/slack → 404),
// so its mark is inlined. Rendered in the same muted foreground as the rest.
function SlackMark() {
  return (
    <svg viewBox="0 0 24 24" width={20} height={20} fill="#9ca3af" aria-hidden>
      <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
    </svg>
  )
}

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
                <span className="inline-flex h-[20px] w-[20px] items-center justify-center opacity-70 transition-opacity group-hover:opacity-100">
                  {logo.slug === 'slack' ? (
                    <SlackMark />
                  ) : (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={`https://cdn.simpleicons.org/${logo.slug}/9ca3af`}
                      alt={logo.name}
                      width={20}
                      height={20}
                      loading="lazy"
                      className="h-[20px] w-[20px]"
                    />
                  )}
                </span>
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

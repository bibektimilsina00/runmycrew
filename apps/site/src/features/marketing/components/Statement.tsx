import { Container } from '@/shared/components/Container'
import { Reveal } from '@/shared/components/Reveal'
import { STATEMENT, STATEMENT_FIGS } from '../data/site'
import { TriggerGlyph, LogicGlyph, ActionsGlyph } from './StatementGlyphs'

const GLYPHS = [TriggerGlyph, LogicGlyph, ActionsGlyph] as const

/**
 * Two-tone statement headline + three FIG tiles. Each tile gets a real
 * diagram-style glyph instead of the placeholder rotated diamond. The
 * tiles fade up in sequence as they enter the viewport, with a soft
 * accent gradient washing across the strip behind them.
 */
export function Statement() {
  return (
    <section className="pt-[104px]">
      <Container className="max-w-[1280px] px-7">
        <Reveal>
          <h2 className="m-0 max-w-[960px] text-[clamp(22px,2.2vw,32px)] font-[590] leading-[1.33] tracking-[-0.012em] text-balance">
            <span className="text-foreground">{STATEMENT.lead}</span>{' '}
            <span className="text-muted-foreground/70">{STATEMENT.trail}</span>
          </h2>
        </Reveal>

        <div className="relative mt-16 border-t border-border/80 pt-[26px]">
          <div className="grid grid-cols-1 gap-[18px] md:grid-cols-3">
            {STATEMENT_FIGS.map((f, i) => {
              const Glyph = GLYPHS[i] ?? TriggerGlyph
              return (
                <Reveal key={f.tag} delay={i * 0.08}>
                  <div className="group">
                    <div className="mb-[18px] font-mono text-[11px] tracking-[0.06em] text-muted-foreground/60">
                      {f.tag}
                    </div>
                    <div className="relative grid h-[200px] place-items-center overflow-hidden rounded-[14px] border border-white/[0.07] bg-gradient-to-br from-white/[0.03] to-transparent transition-colors duration-500 group-hover:border-white/[0.12]">
                      {/* Canvas dot-grid — reads the tile as a mini builder surface. */}
                      <div
                        aria-hidden
                        className="pointer-events-none absolute inset-0 opacity-[0.5]"
                        style={{
                          backgroundImage:
                            'radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px)',
                          backgroundSize: '18px 18px',
                          maskImage:
                            'radial-gradient(120% 90% at 50% 45%, black 40%, transparent 85%)',
                        }}
                      />
                      {/* Top-edge sheen on hover */}
                      <div
                        aria-hidden
                        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/[0.25] to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100"
                      />
                      <Glyph className="relative h-auto w-[78%] text-primary transition-transform duration-700 ease-out group-hover:scale-[1.03]" />
                    </div>
                    <div className="mt-3.5 text-[14px] leading-[1.5] text-muted-foreground/85">
                      {f.body}
                    </div>
                  </div>
                </Reveal>
              )
            })}
          </div>
        </div>
      </Container>
    </section>
  )
}

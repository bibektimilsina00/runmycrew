/**
 * RunMyCrew brand mark — three petals (0°, 120°, 240°) at descending
 * opacity (1.0 / 0.66 / 0.4) around a centre cap. Petals use
 * `currentColor`, so the mark inherits its accent from its parent —
 * set `text-primary`, `text-foreground`, etc on the wrapper.
 *
 * Pass `spin` to play the 7s rotation loop (used on the hero); leave
 * it off for static surfaces (nav, footer, dashboard mocks).
 */
const PETAL = 'M16 16 C 12.4 13, 12.4 6.4, 16 3 C 19.6 6.4, 19.6 13, 16 16 Z'

export function BrandMark({
  className,
  spin = false,
}: {
  className?: string
  spin?: boolean
}) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-hidden>
      <g
        style={
          spin
            ? {
                transformOrigin: '16px 16px',
                animation: 'rmcSpin 7s linear infinite',
              }
            : undefined
        }
      >
        <path d={PETAL} fill="currentColor" />
        <path d={PETAL} fill="currentColor" opacity="0.66" transform="rotate(120 16 16)" />
        <path d={PETAL} fill="currentColor" opacity="0.4" transform="rotate(240 16 16)" />
      </g>
      <circle cx="16" cy="16" r="2.4" fill="var(--background, #0c0d0f)" />
    </svg>
  )
}

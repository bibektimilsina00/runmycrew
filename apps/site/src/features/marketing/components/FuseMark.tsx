/**
 * Fuse brand mark — two overlapping rounded squares (back layer
 * semi-transparent, front layer solid). Both rectangles use
 * `currentColor` via `fill="currentColor"`, so the mark inherits its
 * tone from its parent — set `text-primary`, `text-white`, etc on the
 * wrapper to recolour.
 */
export function FuseMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-hidden>
      <rect x="4"  y="4"  width="17" height="17" rx="6" fill="currentColor" opacity="0.42" />
      <rect x="11" y="11" width="17" height="17" rx="6" fill="currentColor" />
    </svg>
  )
}

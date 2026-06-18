/**
 * Three diagram-grade glyphs for the Statement section's FIG tiles.
 * Replaces the placeholder rotated diamond from the design with real
 * vector art at the same 150px tile size. Strokes inherit
 * `currentColor` so the parent can tone them via Tailwind classes.
 *
 * The grain comes from inline radial gradients + dashed-line accents —
 * cheap to render, no rasters, scales infinitely.
 */

const COMMON = {
  width: 150,
  height: 150,
  viewBox: '0 0 150 150',
  fill: 'none' as const,
}

/** Trigger glyph — a pulse heading into a node, three radial waves. */
export function TriggerGlyph({ className }: { className?: string }) {
  return (
    <svg {...COMMON} className={className}>
      <defs>
        <radialGradient id="t-grad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.45" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
      </defs>
      {/* Halo */}
      <circle cx="75" cy="75" r="56" fill="url(#t-grad)" opacity="0.35" />
      {/* Three concentric pulses */}
      <circle cx="42" cy="75" r="18" stroke="currentColor" strokeOpacity="0.45" strokeWidth="1" />
      <circle cx="42" cy="75" r="11" stroke="currentColor" strokeOpacity="0.7"  strokeWidth="1" />
      <circle cx="42" cy="75" r="5"  fill="currentColor" />
      {/* Connector */}
      <line x1="55" y1="75" x2="92" y2="75" stroke="currentColor" strokeOpacity="0.4" strokeWidth="1" strokeDasharray="3 4" />
      {/* Target node */}
      <rect x="92" y="58" width="36" height="34" rx="6" stroke="currentColor" strokeOpacity="0.65" strokeWidth="1" />
      <rect x="100" y="68" width="20" height="3" rx="1" fill="currentColor" opacity="0.5" />
      <rect x="100" y="76" width="14" height="3" rx="1" fill="currentColor" opacity="0.3" />
    </svg>
  )
}

/** Logic glyph — branching decision with two paths. */
export function LogicGlyph({ className }: { className?: string }) {
  return (
    <svg {...COMMON} className={className}>
      <defs>
        <radialGradient id="l-grad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.4" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="75" cy="75" r="56" fill="url(#l-grad)" opacity="0.3" />
      {/* Source */}
      <rect x="20" y="63" width="30" height="24" rx="5" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1" />
      <circle cx="35" cy="75" r="2.5" fill="currentColor" />
      {/* Splitter diamond */}
      <g transform="translate(75 75) rotate(45)">
        <rect x="-13" y="-13" width="26" height="26" stroke="currentColor" strokeOpacity="0.7" strokeWidth="1" fill="currentColor" fillOpacity="0.08" />
      </g>
      {/* Two branch lines */}
      <path d="M50 75 H62" stroke="currentColor" strokeOpacity="0.5" strokeWidth="1" />
      <path d="M88 65 C100 55 108 50 120 50" stroke="currentColor" strokeOpacity="0.5" strokeWidth="1" strokeDasharray="3 4" />
      <path d="M88 85 C100 95 108 100 120 100" stroke="currentColor" strokeOpacity="0.5" strokeWidth="1" strokeDasharray="3 4" />
      {/* Two target nodes */}
      <rect x="120" y="40" width="22" height="20" rx="4" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1" />
      <rect x="120" y="90" width="22" height="20" rx="4" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1" />
    </svg>
  )
}

/** Actions glyph — one source fanning to four targets. */
export function ActionsGlyph({ className }: { className?: string }) {
  return (
    <svg {...COMMON} className={className}>
      <defs>
        <radialGradient id="a-grad" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.4" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="75" cy="75" r="56" fill="url(#a-grad)" opacity="0.3" />
      {/* Source node */}
      <rect x="14" y="63" width="32" height="24" rx="5" stroke="currentColor" strokeOpacity="0.7" strokeWidth="1" fill="currentColor" fillOpacity="0.06" />
      <circle cx="30" cy="75" r="3" fill="currentColor" />
      {/* Four fan-out lines */}
      <path d="M46 75 C70 75 90 30 116 30" stroke="currentColor" strokeOpacity="0.45" strokeWidth="1" strokeDasharray="3 4" />
      <path d="M46 75 C70 75 90 56 116 56" stroke="currentColor" strokeOpacity="0.5"  strokeWidth="1" strokeDasharray="3 4" />
      <path d="M46 75 C70 75 90 94 116 94" stroke="currentColor" strokeOpacity="0.5"  strokeWidth="1" strokeDasharray="3 4" />
      <path d="M46 75 C70 75 90 120 116 120" stroke="currentColor" strokeOpacity="0.45" strokeWidth="1" strokeDasharray="3 4" />
      {/* Four targets */}
      <rect x="116" y="22"  width="22" height="16" rx="3.5" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1" />
      <rect x="116" y="48"  width="22" height="16" rx="3.5" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1" />
      <rect x="116" y="86"  width="22" height="16" rx="3.5" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1" />
      <rect x="116" y="112" width="22" height="16" rx="3.5" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1" />
    </svg>
  )
}

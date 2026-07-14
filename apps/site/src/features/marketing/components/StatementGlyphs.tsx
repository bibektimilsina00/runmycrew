/**
 * Three node-diagram glyphs for the Statement section's FIG tiles, sharing
 * one visual grammar so the strip reads as a coherent workflow pipeline —
 * Triggers → Logic → Actions — rather than three unrelated sketches.
 *
 * Grammar (identical across all three):
 *   • Landscape 220×140 canvas, content flows left → right.
 *   • Spine — the main node + its connectors — uses `currentColor` (the
 *     parent tones it with the brand accent) so the eye follows the flow.
 *   • Peripheral chips use neutral white strokes.
 *   • Nodes: rounded rects, faint fill + hairline border. Connectors:
 *     dashed. No per-glyph radial blobs — the tile supplies the ambience.
 */

const COMMON = {
  viewBox: '0 0 220 140',
  fill: 'none' as const,
}

const NEUTRAL = 'rgba(255,255,255,0.14)'
const NEUTRAL_SOFT = 'rgba(255,255,255,0.06)'
const LINE = 'rgba(255,255,255,0.2)'

/** A small chip icon: a rounded square with two text-line marks. */
function Chip({ x, y, accent = false }: { x: number; y: number; accent?: boolean }) {
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect
        width="30"
        height="24"
        rx="6"
        fill={accent ? 'currentColor' : NEUTRAL_SOFT}
        fillOpacity={accent ? 0.1 : 1}
        stroke={accent ? 'currentColor' : NEUTRAL}
        strokeOpacity={accent ? 0.7 : 1}
        strokeWidth="1"
      />
      <rect x="7" y="8" width="16" height="2.5" rx="1.25" fill="currentColor" opacity="0.45" />
      <rect x="7" y="14" width="10" height="2.5" rx="1.25" fill="currentColor" opacity="0.25" />
    </g>
  )
}

/** Triggers — three source types (event · webhook · schedule) converge into
 *  the workflow's start node. */
export function TriggerGlyph({ className }: { className?: string }) {
  const srcY = [30, 58, 86] // three stacked sources
  return (
    <svg {...COMMON} className={className}>
      {/* Three source chips on the left */}
      {srcY.map((y) => (
        <g key={y}>
          <rect x="18" y={y} width="26" height="24" rx="6" fill={NEUTRAL_SOFT} stroke={NEUTRAL} strokeWidth="1" />
          <circle cx="31" cy={y + 12} r="2.5" fill="currentColor" opacity="0.55" />
        </g>
      ))}
      {/* Converging connectors into the start node (spine, accent) */}
      <path d={`M44 ${srcY[0] + 12} C80 ${srcY[0] + 12} 96 70 120 70`} stroke="currentColor" strokeOpacity="0.45" strokeWidth="1.25" strokeDasharray="3 4" />
      <path d={`M44 ${srcY[1] + 12} H120`} stroke="currentColor" strokeOpacity="0.55" strokeWidth="1.25" strokeDasharray="3 4" />
      <path d={`M44 ${srcY[2] + 12} C80 ${srcY[2] + 12} 96 70 120 70`} stroke="currentColor" strokeOpacity="0.45" strokeWidth="1.25" strokeDasharray="3 4" />
      {/* Start node */}
      <rect x="120" y="52" width="82" height="36" rx="8" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeOpacity="0.7" strokeWidth="1" />
      <circle cx="136" cy="70" r="4.5" fill="currentColor" />
      <rect x="148" y="64" width="40" height="3" rx="1.5" fill="currentColor" opacity="0.45" />
      <rect x="148" y="72" width="26" height="3" rx="1.5" fill="currentColor" opacity="0.28" />
    </svg>
  )
}

/** Logic — a node routes through a condition that branches into two paths. */
export function LogicGlyph({ className }: { className?: string }) {
  return (
    <svg {...COMMON} className={className}>
      {/* Source node (spine) */}
      <rect x="10" y="52" width="42" height="36" rx="8" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeOpacity="0.7" strokeWidth="1" />
      <circle cx="24" cy="70" r="3.5" fill="currentColor" />
      <rect x="33" y="66" width="12" height="3" rx="1.5" fill="currentColor" opacity="0.4" />
      {/* Connector to the condition */}
      <path d="M52 70 H82" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1.25" strokeDasharray="3 4" />
      {/* Condition diamond */}
      <g transform="translate(102 70) rotate(45)">
        <rect x="-15" y="-15" width="30" height="30" rx="4" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeOpacity="0.7" strokeWidth="1" />
      </g>
      {/* Two branch connectors */}
      <path d="M122 62 C142 48 150 40 168 40" stroke={LINE} strokeWidth="1.25" strokeDasharray="3 4" />
      <path d="M122 78 C142 92 150 100 168 100" stroke={LINE} strokeWidth="1.25" strokeDasharray="3 4" />
      {/* Two outcome chips */}
      <Chip x={168} y={28} />
      <Chip x={168} y={88} />
    </svg>
  )
}

/** Actions — one node fans out to four connected tools in a single run. */
export function ActionsGlyph({ className }: { className?: string }) {
  const outY = [16, 44, 72, 100] // chip tops; centres 28/56/84/112 stay inside the 140 canvas
  return (
    <svg {...COMMON} className={className}>
      {/* Source node (spine) */}
      <rect x="12" y="52" width="46" height="36" rx="8" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeOpacity="0.7" strokeWidth="1" />
      <circle cx="28" cy="70" r="4" fill="currentColor" />
      <rect x="38" y="66" width="12" height="3" rx="1.5" fill="currentColor" opacity="0.4" />
      {/* Four fan-out connectors */}
      {outY.map((y) => (
        <path
          key={y}
          d={`M58 70 C104 70 130 ${y + 12} 176 ${y + 12}`}
          stroke="currentColor"
          strokeOpacity="0.4"
          strokeWidth="1.25"
          strokeDasharray="3 4"
        />
      ))}
      {/* Four tool chips */}
      {outY.map((y) => (
        <Chip key={y} x={176} y={y} />
      ))}
    </svg>
  )
}

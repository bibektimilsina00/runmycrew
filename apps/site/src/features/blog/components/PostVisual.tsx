import type { BlogPost } from '../data/posts'

/**
 * Renders a per-post hero illustration. Pure SVG (no rasters) so the
 * cards stay crisp at any size and don't need a CDN. Each variant uses
 * brand tokens so they re-tint with the active scheme.
 */
export function PostVisual({ which }: { which: BlogPost['visual'] }) {
  if (which === 'crew-ai')      return <CrewAiVisual />
  if (which === 'enterprise')   return <EnterpriseVisual />
  if (which === 'series')       return <SeriesVisual />
  if (which === 'realtime')     return <RealtimeVisual />
  if (which === 'executor')     return <ExecutorVisual />
  if (which === 'agent-loops')  return <AgentLoopsVisual />
  return <MothershipVisual />
}

function AgentLoopsVisual() {
  return (
    <svg viewBox="0 0 600 320" className="h-full w-full">
      <defs>
        <linearGradient id="bg-loops" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%"   stopColor="#202a55" />
          <stop offset="100%" stopColor="#08090a" />
        </linearGradient>
        <linearGradient id="rim-loops" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%"  stopColor="#7aa2f7" />
          <stop offset="50%" stopColor="#4cc38a" />
          <stop offset="100%" stopColor="#e5b341" />
        </linearGradient>
      </defs>
      <rect width="600" height="320" fill="url(#bg-loops)" />

      {/* Cron tick markers along the top */}
      <g stroke="rgba(255,255,255,0.35)" strokeWidth="1.2">
        {Array.from({ length: 12 }).map((_, i) => (
          <line key={i} x1={60 + i * 40} y1="40" x2={60 + i * 40} y2="56" />
        ))}
      </g>

      {/* The loop ring */}
      <g transform="translate(300,180)" fill="none">
        <circle r="86" stroke="url(#rim-loops)" strokeWidth="2.2" />
        <circle r="62" stroke="rgba(255,255,255,0.18)" strokeWidth="0.6" />
      </g>

      {/* Three tool-call dots on the ring (one per "iteration") */}
      <g>
        <circle cx="386" cy="180" r="6" fill="#7aa2f7" />
        <circle cx="300" cy="94"  r="6" fill="#4cc38a" />
        <circle cx="214" cy="180" r="6" fill="#e5b341" />
      </g>

      {/* Budget meter at bottom */}
      <g transform="translate(60,278)">
        <rect width="480" height="6" rx="3" fill="rgba(255,255,255,0.1)" />
        <rect width="320" height="6" rx="3" fill="url(#rim-loops)" />
      </g>
    </svg>
  )
}

function CrewAiVisual() {
  return (
    <svg viewBox="0 0 600 320" className="h-full w-full">
      <defs>
        <linearGradient id="bg-ai" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%"   stopColor="#5e6ad2" />
          <stop offset="60%"  stopColor="#3a3f7d" />
          <stop offset="100%" stopColor="#08090a" />
        </linearGradient>
      </defs>
      <rect width="600" height="320" fill="url(#bg-ai)" />
      <g fill="#fff" opacity="0.5">
        {Array.from({ length: 60 }).map((_, i) => (
          <circle key={i} cx={(i * 47) % 600} cy={(i * 53) % 320} r={i % 4 === 0 ? 2 : 1} />
        ))}
      </g>
      <g transform="translate(260,110)">
        <rect x="0"  y="0"  width="56" height="56" rx="14" fill="#fff" opacity="0.45" />
        <rect x="22" y="22" width="56" height="56" rx="14" fill="#fff" />
      </g>
    </svg>
  )
}

function EnterpriseVisual() {
  return (
    <svg viewBox="0 0 600 320" className="h-full w-full">
      <rect width="600" height="320" fill="#0a0b0c" />
      <g transform="translate(60,80)">
        {Array.from({ length: 5 }).map((_, i) => (
          <rect key={i} x={i * 100} y="0" width="84" height="160" rx="10" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.12)" strokeWidth="0.6" />
        ))}
      </g>
      <g transform="translate(60,260)">
        <rect width="480" height="6" rx="3" fill="url(#rb)" />
        <defs>
          <linearGradient id="rb" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%"   stopColor="#5e6ad2" />
            <stop offset="25%"  stopColor="#7aa2f7" />
            <stop offset="50%"  stopColor="#4cc38a" />
            <stop offset="75%"  stopColor="#e5b341" />
            <stop offset="100%" stopColor="#e5675f" />
          </linearGradient>
        </defs>
      </g>
    </svg>
  )
}

function SeriesVisual() {
  return (
    <svg viewBox="0 0 600 320" className="h-full w-full">
      <rect width="600" height="320" fill="#0a0b0c" />
      <g transform="translate(60,80)" fill="#fff">
        <rect width="34" height="34" rx="8" opacity="0.45" />
        <rect x="20" y="20" width="34" height="34" rx="8" />
      </g>
      <text x="124" y="116" fontFamily="JetBrains Mono, monospace" fontSize="26" fill="#fff" fontWeight="600">$8M · Seed</text>
      <g transform="translate(60,170)">
        <rect width="480" height="80" rx="10" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.12)" strokeWidth="0.6" />
        <text x="20" y="50" fontFamily="Inter, sans-serif" fontSize="16" fill="rgba(255,255,255,0.7)">Standard · SV Angel · Sequoia</text>
      </g>
    </svg>
  )
}

function RealtimeVisual() {
  return (
    <svg viewBox="0 0 600 320" className="h-full w-full">
      <rect width="600" height="320" fill="#0a0b0c" />
      <g>
        <circle cx="170" cy="120" r="34" fill="#5e6ad2" opacity="0.85" />
        <circle cx="300" cy="160" r="28" fill="#4cc38a" opacity="0.85" />
        <circle cx="420" cy="90"  r="32" fill="#e5b341" opacity="0.85" />
        <circle cx="460" cy="200" r="24" fill="#e5675f" opacity="0.85" />
      </g>
      <g stroke="rgba(255,255,255,0.22)" strokeWidth="0.8" fill="none">
        <path d="M170 120 L300 160 L420 90 L460 200" />
      </g>
    </svg>
  )
}

function ExecutorVisual() {
  return (
    <svg viewBox="0 0 600 320" className="h-full w-full">
      <rect width="600" height="320" fill="#0a0b0c" />
      <g stroke="rgba(255,255,255,0.18)" strokeWidth="0.5" fill="none">
        {Array.from({ length: 20 }).map((_, i) => (
          <line key={i} x1={20 + i * 30} y1="20" x2={20 + i * 30} y2="300" />
        ))}
        {Array.from({ length: 12 }).map((_, i) => (
          <line key={i} x1="20" y1={20 + i * 24} x2="580" y2={20 + i * 24} />
        ))}
      </g>
      <g fill="#5e6ad2" opacity="0.9">
        {[2, 5, 8, 11, 14, 17].map((c, i) => (
          <rect key={i} x={20 + c * 30 - 10} y={20 + i * 24 - 7} width="20" height="14" rx="3" />
        ))}
      </g>
    </svg>
  )
}

function MothershipVisual() {
  return (
    <svg viewBox="0 0 600 320" className="h-full w-full">
      <defs>
        <linearGradient id="bg-m" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%"   stopColor="#1a2547" />
          <stop offset="100%" stopColor="#08090a" />
        </linearGradient>
      </defs>
      <rect width="600" height="320" fill="url(#bg-m)" />
      <ellipse cx="300" cy="140" rx="120" ry="34" fill="rgba(255,255,255,0.9)" />
      <text x="231" y="148" fontFamily="Inter, sans-serif" fontSize="18" fontWeight="700" fill="#08090a">RunMyCrew</text>
      <g stroke="rgba(255,255,255,0.4)" strokeWidth="0.8" fill="none">
        <path d="M0 220 L600 200" />
        <path d="M0 240 L600 220" />
        <path d="M0 260 L600 240" />
      </g>
    </svg>
  )
}

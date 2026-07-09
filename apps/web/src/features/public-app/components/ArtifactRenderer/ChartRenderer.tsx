import type { RendererProps } from './types'

interface Series {
  name: string
  data: Array<{ x: string | number; y: number }>
  color?: string
}

/**
 * Minimal native SVG chart — no chart library dep in the public bundle.
 * Supports line + bar. Enough for run-time previews; owners who need
 * pixel-perfect charts can emit a `code` artifact with a Vega/Plotly
 * spec instead.
 */
export function ChartRenderer({ artifact }: RendererProps) {
  const kind = String(artifact.data?.type ?? 'line')
  const series = (artifact.data?.series as Series[]) ?? []
  const width = 640
  const height = 320
  const padding = { top: 20, right: 20, bottom: 40, left: 44 }

  if (series.length === 0)
    return <div className="p-6 text-[13px] text-white/50">Empty chart</div>

  const allPoints = series.flatMap(s => s.data)
  const xs = allPoints.map(p => p.x)
  const ys = allPoints.map(p => p.y)
  const minY = Math.min(0, ...ys)
  const maxY = Math.max(...ys, 1)
  const yScale = (v: number) =>
    height - padding.bottom - ((v - minY) / (maxY - minY)) * (height - padding.top - padding.bottom)
  const xScale = (i: number) =>
    padding.left + (i / Math.max(xs.length - 1, 1)) * (width - padding.left - padding.right)

  return (
    <div className="flex h-full flex-col p-6">
      {artifact.title && (
        <div className="mb-2 text-[13px] font-semibold text-white">{artifact.title}</div>
      )}
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-auto w-full flex-1"
        preserveAspectRatio="xMidYMid meet"
      >
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
          stroke="rgba(255,255,255,0.15)"
        />
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
          stroke="rgba(255,255,255,0.15)"
        />
        {series.map((s, si) => {
          const color = s.color || (si === 0 ? 'var(--app-accent,#8b5cf6)' : '#38bdf8')
          if (kind === 'bar') {
            const barWidth = ((width - padding.left - padding.right) / s.data.length) * 0.7
            return (
              <g key={s.name}>
                {s.data.map((p, i) => (
                  <rect
                    key={i}
                    x={xScale(i) - barWidth / 2}
                    y={yScale(p.y)}
                    width={barWidth}
                    height={height - padding.bottom - yScale(p.y)}
                    fill={color}
                    opacity={0.8}
                  />
                ))}
              </g>
            )
          }
          const d = s.data
            .map((p, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(p.y)}`)
            .join(' ')
          return (
            <g key={s.name}>
              <path d={d} fill="none" stroke={color} strokeWidth={2} />
              {s.data.map((p, i) => (
                <circle key={i} cx={xScale(i)} cy={yScale(p.y)} r={2.5} fill={color} />
              ))}
            </g>
          )
        })}
      </svg>
      {series.length > 1 && (
        <div className="mt-2 flex flex-wrap gap-3 text-[11.5px] text-white/60">
          {series.map((s, si) => (
            <div key={s.name} className="flex items-center gap-1.5">
              <span
                className="h-2 w-3 rounded-sm"
                style={{ background: s.color || (si === 0 ? 'var(--app-accent,#8b5cf6)' : '#38bdf8') }}
              />
              {s.name}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

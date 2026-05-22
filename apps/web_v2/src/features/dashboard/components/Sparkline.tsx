interface SparklineProps {
  data: number[]
  color?: string
  className?: string
}

export function Sparkline({ data, color = 'currentColor', className }: SparklineProps) {
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const w = 70
  const h = 28

  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w
    const y = h - ((v - min) / range) * (h - 4) - 2
    return `${x},${y}`
  }).join(' ')

  const lastVal = data[data.length - 1]
  const lastY = h - ((lastVal - min) / range) * (h - 4) - 2

  return (
    <svg viewBox={`0 0 ${w} ${h}`} fill="none" className={className}>
      <polyline points={pts} stroke={color} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
      <circle cx={w} cy={lastY} r="1.8" fill={color} />
    </svg>
  )
}

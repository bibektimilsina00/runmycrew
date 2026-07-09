import type { SuggestedPrompt } from '../types/publicAppTypes'

interface SuggestedPromptsProps {
  items: SuggestedPrompt[]
  onPick: (prompt: string) => void
}

export function SuggestedPrompts({ items, onPick }: SuggestedPromptsProps) {
  if (items.length === 0) return null
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {items.map((p, i) => (
        <button
          key={`${p.label}-${i}`}
          onClick={() => onPick(p.prompt)}
          className="rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1.5 text-[12.5px] text-white/75 transition hover:border-white/25 hover:bg-white/[0.08] hover:text-white"
        >
          {p.label || p.prompt}
        </button>
      ))}
    </div>
  )
}

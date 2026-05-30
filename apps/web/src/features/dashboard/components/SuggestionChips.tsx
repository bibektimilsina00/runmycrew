interface SuggestionChipsProps {
  suggestions: string[]
  onPick: (text: string) => void
  disabled?: boolean
}

/** A row of tappable example prompts that fill the input. */
export function SuggestionChips({ suggestions, onPick, disabled }: SuggestionChipsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {suggestions.map(s => (
        <button
          key={s}
          type="button"
          onClick={() => onPick(s)}
          disabled={disabled}
          className="rounded-full border border-[var(--border-faint)] bg-[var(--surface)]/40 px-3.5 py-1.5 text-[12px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {s.length > 64 ? `${s.slice(0, 64)}…` : s}
        </button>
      ))}
    </div>
  )
}

import { Sparkles } from 'lucide-react'
import { SuggestedPrompts } from './SuggestedPrompts'
import type { PublicApp } from '../types/publicAppTypes'

interface WelcomeStateProps {
  app: PublicApp
  onPickPrompt: (prompt: string) => void
}

/**
 * Empty-state hero shown before the first message. Big headline centered,
 * suggested prompts below. Draws focus to the input bar.
 */
export function WelcomeState({ app, onPickPrompt }: WelcomeStateProps) {
  const headline = app.config.welcome_headline || `Talk to ${app.title}`
  const sub = app.config.welcome_sub || app.description || ''
  const suggestions = app.config.suggested_prompts ?? []
  return (
    <div className="mx-auto flex max-w-[720px] flex-1 flex-col items-center justify-center gap-5 px-6 py-16 text-center">
      <span
        className="flex h-11 w-11 items-center justify-center rounded-[14px]"
        style={{
          background: 'color-mix(in oklab, var(--app-accent, #8b5cf6) 15%, transparent)',
          color: 'var(--app-accent, #8b5cf6)',
        }}
      >
        <Sparkles size={20} />
      </span>
      <div>
        <h1 className="text-[26px] font-semibold leading-tight tracking-tight text-white">
          {headline}
        </h1>
        {sub && (
          <p className="mt-2 max-w-[520px] text-[13.5px] leading-relaxed text-white/55">{sub}</p>
        )}
      </div>
      <SuggestedPrompts items={suggestions} onPick={onPickPrompt} />
    </div>
  )
}

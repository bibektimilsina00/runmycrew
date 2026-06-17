import { Check } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useColorScheme, type ColorScheme } from '@/stores/theme'

interface SchemeSwatch {
  id: ColorScheme
  label: string
  /** CSS background string for the swatch — composes app + accent. */
  app: string
  accent: string
}

const SWATCHES: SchemeSwatch[] = [
  { id: 'linear',  label: 'Linear',  app: '#08090a', accent: '#5e6ad2' },
  { id: 'slate',   label: 'Slate',   app: '#0e0f12', accent: '#6b76e0' },
  { id: 'indigo',  label: 'Indigo',  app: '#08090c', accent: '#7c83ff' },
  { id: 'emerald', label: 'Emerald', app: '#070908', accent: '#3fb98a' },
  { id: 'ember',   label: 'Ember',   app: '#0a0807', accent: '#e0673f' },
  { id: 'plum',    label: 'Plum',    app: '#09080a', accent: '#a06cf0' },
]

export function AppearanceCard() {
  const { scheme, setScheme } = useColorScheme()

  return (
    <section className="border border-[var(--border-soft)] rounded-[12px] bg-[var(--surface)] overflow-hidden">
      <header className="flex items-center gap-[10px] px-[20px] py-[14px] border-b border-[var(--border-faint)]">
        <span className="text-[13.5px] font-semibold text-[var(--text)]">Appearance</span>
        <span className="text-[12px] text-[var(--text-faint)]">Color scheme used across the app.</span>
      </header>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-[12px] p-[20px]">
        {SWATCHES.map(s => {
          const active = scheme === s.id
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => setScheme(s.id)}
              className={cn(
                'group relative flex flex-col gap-[8px] p-[10px] rounded-[10px] border transition-colors text-left cursor-pointer',
                active
                  ? 'border-[var(--accent)] bg-[var(--accent-soft)]'
                  : 'border-[var(--border-soft)] bg-[rgba(255,255,255,0.015)] hover:border-[var(--border)] hover:bg-[rgba(255,255,255,0.04)]',
              )}
            >
              <span
                className="block w-full h-[44px] rounded-[7px] relative overflow-hidden border border-[rgba(255,255,255,0.05)]"
                style={{ background: s.app }}
              >
                <span
                  className="absolute right-[8px] bottom-[8px] w-[16px] h-[16px] rounded-[5px] shadow-[0_2px_6px_rgba(0,0,0,0.4)]"
                  style={{ background: s.accent }}
                />
                <span
                  className="absolute left-[8px] top-[8px] w-[28px] h-[6px] rounded-full"
                  style={{ background: 'rgba(255,255,255,0.06)' }}
                />
                <span
                  className="absolute left-[8px] top-[18px] w-[40px] h-[5px] rounded-full"
                  style={{ background: 'rgba(255,255,255,0.04)' }}
                />
              </span>
              <span className="flex items-center justify-between">
                <span className="text-[12.5px] font-medium text-[var(--text)]">{s.label}</span>
                {active && (
                  <Check className="w-[13px] h-[13px] text-[var(--accent)]" strokeWidth={2.5} />
                )}
              </span>
            </button>
          )
        })}
      </div>
    </section>
  )
}

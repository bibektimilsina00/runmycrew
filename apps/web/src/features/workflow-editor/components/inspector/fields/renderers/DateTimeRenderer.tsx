import { useRef, type ChangeEvent } from 'react'
import { Calendar } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { RendererProps } from '../types'

/**
 * Datetime field renderer — both **typeable** and **pickable**.
 *
 * The visible input is a plain text field, so users can paste expressions
 * (`{{ $trigger.date }}`) or hand-type a literal value. A trailing
 * calendar icon opens the browser's native date / date-time picker via
 * `HTMLInputElement.showPicker()`; the picked value is normalised back
 * to the canonical shape and written into the text field.
 *
 * typeOptions:
 *   - `granularity`: "date" (default) → emits `YYYY-MM-DD`
 *                    "datetime"      → emits `YYYY-MM-DDTHH:MM:00Z`
 */

type Granularity = 'date' | 'datetime'

function getGranularity(prop: RendererProps['prop']): Granularity {
  const g = (prop.typeOptions ?? {}).granularity
  return g === 'datetime' ? 'datetime' : 'date'
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

/** Convert the field's stored text to the shape the native picker
 *  expects (`YYYY-MM-DD` for date, `YYYY-MM-DDTHH:MM` for datetime-local).
 *  Expressions and unparseable inputs return `''` so the picker opens
 *  on today rather than blowing up. */
function parseForNative(text: string, granularity: Granularity): string {
  if (!text || text.includes('{{')) return ''

  if (granularity === 'date') {
    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return text
    const d = new Date(text)
    if (isNaN(d.getTime())) return ''
    return d.toISOString().slice(0, 10)
  }

  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(text)) return text
  const d = new Date(text)
  if (isNaN(d.getTime())) return ''
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  )
}

export function DateTimeRenderer({
  prop,
  value,
  onChange,
  disabled,
}: RendererProps) {
  const granularity = getGranularity(prop)
  const text = typeof value === 'string' ? value : ''
  const nativeRef = useRef<HTMLInputElement>(null)

  const openPicker = () => {
    const el = nativeRef.current
    if (!el) return
    // Modern browsers support `showPicker()`; fallback to focus + click.
    const elWithPicker = el as HTMLInputElement & { showPicker?: () => void }
    if (typeof elWithPicker.showPicker === 'function') {
      try {
        elWithPicker.showPicker()
        return
      } catch {
        // Some browsers throw if the element isn't focused — fall through.
      }
    }
    el.focus()
    el.click()
  }

  const onNativePick = (e: ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    if (!v) return
    if (granularity === 'datetime') {
      onChange(`${v}:00Z`)
    } else {
      onChange(v)
    }
  }

  const placeholder =
    prop.placeholder ||
    (granularity === 'datetime' ? '2026-05-15T14:30:00Z' : '2026-05-15')

  return (
    <div className="relative">
      <input
        type="text"
        value={text}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          'w-full rounded-[6px] border border-border-faint bg-surface',
          'pl-2.5 pr-8 py-1.5 text-[12px] text-text outline-none',
          'placeholder:text-text-faint',
          'focus:border-accent',
          disabled && 'cursor-not-allowed opacity-50',
        )}
      />
      <button
        type="button"
        onClick={openPicker}
        disabled={disabled}
        title="Pick a date"
        className={cn(
          'absolute right-1.5 top-1/2 -translate-y-1/2',
          'flex h-6 w-6 items-center justify-center rounded-[4px]',
          'text-text-faint hover:bg-surface-2 hover:text-text',
          'transition-colors',
          disabled && 'cursor-not-allowed opacity-50',
        )}
      >
        <Calendar className="h-3.5 w-3.5" />
      </button>
      {/* Hidden native picker — visually 0×0 but interactive so
          showPicker() can pop the calendar over the text input. */}
      <input
        ref={nativeRef}
        type={granularity === 'datetime' ? 'datetime-local' : 'date'}
        value={parseForNative(text, granularity)}
        onChange={onNativePick}
        disabled={disabled}
        tabIndex={-1}
        aria-hidden="true"
        className={cn(
          'absolute right-1.5 top-1/2 -translate-y-1/2',
          'h-0 w-0 opacity-0 pointer-events-none',
        )}
      />
    </div>
  )
}

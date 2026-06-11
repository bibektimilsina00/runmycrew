import { useState, useRef, useEffect, useMemo } from 'react'
import { Check, ChevronDown, Loader2, X } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { NodePropertyOption } from '../../../../types/editorTypes'
import { useLoadOptions } from '../../hooks/use-load-options'
import type { RendererProps } from '../types'

/**
 * `OptionsRenderer` handles three shapes:
 *   - `options` single-select dropdown
 *   - `options` searchable / allow-custom combobox
 *   - `multi-options` checkbox-style multi-select (chips + dropdown)
 *
 * Multi-select is detected by `prop.type === 'multi-options'`.
 */
export function OptionsRenderer({ prop, value, onChange, properties, disabled }: RendererProps) {
  const { data: dynamicOptions = [], isLoading } = useLoadOptions(
    prop.loadOptions,
    prop.loadOptionsDependsOn,
    properties,
  )

  const allOptions: NodePropertyOption[] = useMemo(
    () => [...dynamicOptions, ...(prop.options ?? [])],
    [dynamicOptions, prop.options],
  )

  const isMulti = prop.type === 'multi-options'
  const allowCustom = prop.typeOptions?.allowCustom ?? false
  const searchable  = prop.typeOptions?.searchable ?? false

  if (isMulti) {
    return (
      <MultiSelect
        options={allOptions}
        value={value}
        onChange={onChange}
        placeholder={prop.placeholder ?? `Select ${prop.label}`}
        isLoading={isLoading}
        disabled={disabled}
      />
    )
  }

  const selected = allOptions.find(o => String(o.value) === String(value))
  const displayValue = selected?.label ?? (value !== undefined && value !== null ? String(value) : '')

  if (allowCustom || searchable) {
    return (
      <ComboBox
        options={allOptions}
        value={value}
        displayValue={displayValue}
        onChange={onChange}
        placeholder={prop.placeholder ?? `Select or type ${prop.label}`}
        isLoading={isLoading}
        allowCustom={allowCustom}
        disabled={disabled}
      />
    )
  }

  return (
    <SimpleSelect
      options={allOptions}
      value={value}
      onChange={onChange}
      placeholder={prop.placeholder ?? `Select ${prop.label}`}
      isLoading={isLoading}
      disabled={disabled}
    />
  )
}

// ── Simple Select ─────────────────────────────────────────────────────────────

interface SimpleSelectProps {
  options: NodePropertyOption[]
  value: unknown
  onChange: (value: unknown) => void
  placeholder: string
  isLoading: boolean
  disabled?: boolean
}

function SimpleSelect({ options, value, onChange, placeholder, isLoading, disabled }: SimpleSelectProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const selected = options.find(o => String(o.value) === String(value))

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        disabled={disabled}
        className={cn(
          'flex h-8 w-full items-center gap-2 rounded-[8px] border border-border-faint bg-bg px-3 text-[12px] text-left',
          'transition-colors hover:border-border-soft',
          open && 'border-border bg-surface',
          disabled && 'opacity-50 cursor-not-allowed',
        )}
      >
        <span className={cn('flex-1 min-w-0 truncate', !selected && 'text-text-faint')}>
          {isLoading ? 'Loading…' : (selected?.label ?? placeholder)}
        </span>
        {isLoading ? <Loader2 size={12} className="shrink-0 animate-spin text-text-faint" /> : <ChevronDown size={12} className={cn('shrink-0 text-text-faint transition-transform', open && 'rotate-180')} />}
      </button>

      {open && (
        <div className="absolute top-[calc(100%+4px)] left-0 right-0 z-50 max-h-52 overflow-y-auto rounded-[10px] border border-border-faint bg-bg p-1.5 shadow-dropdown">
          {options.length === 0 && (
            <p className="px-2.5 py-2 text-[11px] text-text-faint">No options</p>
          )}
          {options.map((opt, i) => (
            <button
              key={i}
              type="button"
              onClick={() => { onChange(opt.value); setOpen(false) }}
              className={cn(
                'flex w-full items-center gap-2 rounded-[7px] px-2.5 py-1.5 text-left text-[12px]',
                String(opt.value) === String(value) ? 'bg-surface-2 font-medium text-text' : 'text-text-mute hover:bg-surface hover:text-text',
              )}
            >
              <span className="flex-1 min-w-0">
                <span className="block">{opt.label}</span>
                {opt.description && <span className="block text-[10px] text-text-faint">{opt.description}</span>}
              </span>
              {String(opt.value) === String(value) && <Check size={11} className="shrink-0 text-accent" />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── ComboBox (searchable + allowCustom) ───────────────────────────────────────

interface ComboBoxProps {
  options: NodePropertyOption[]
  value: unknown
  displayValue: string
  onChange: (value: unknown) => void
  placeholder: string
  isLoading: boolean
  allowCustom: boolean
  disabled?: boolean
}

function ComboBox({ options, value, displayValue, onChange, placeholder, isLoading, allowCustom, disabled }: ComboBoxProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const ref = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) { setOpen(false); setQuery('') }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const filtered = query
    ? options.filter(o => o.label.toLowerCase().includes(query.toLowerCase()) || String(o.value).toLowerCase().includes(query.toLowerCase()))
    : options

  const handleFocus = () => { setOpen(true); setQuery('') }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    setQuery(v)
    setOpen(true)
    if (allowCustom) onChange(v)
  }

  const handleSelect = (opt: NodePropertyOption) => {
    onChange(opt.value)
    setOpen(false)
    setQuery('')
  }

  const inputValue = open ? query : displayValue

  return (
    <div ref={ref} className="relative">
      <div className="relative flex items-center">
        <input
          ref={inputRef}
          value={inputValue}
          onFocus={handleFocus}
          onChange={handleInputChange}
          placeholder={isLoading ? 'Loading…' : placeholder}
          disabled={disabled}
          className={cn(
            'h-8 w-full rounded-[8px] border border-border-faint bg-bg pl-3 pr-8 text-[12px]',
            'placeholder:text-text-faint transition-colors',
            'focus:outline-none focus:border-border focus:bg-surface',
            disabled && 'opacity-50 cursor-not-allowed',
          )}
          spellCheck={false}
        />
        <div className="pointer-events-none absolute right-2.5 flex items-center">
          {isLoading ? <Loader2 size={12} className="animate-spin text-text-faint" /> : <ChevronDown size={12} className={cn('text-text-faint transition-transform', open && 'rotate-180')} />}
        </div>
      </div>

      {open && (
        <div className="absolute top-[calc(100%+4px)] left-0 right-0 z-50 max-h-52 overflow-y-auto rounded-[10px] border border-border-faint bg-bg p-1.5 shadow-dropdown">
          {filtered.length === 0 && (
            <p className="px-2.5 py-2 text-[11px] text-text-faint">
              {allowCustom && query ? `Use "${query}" as custom value` : 'No options'}
            </p>
          )}
          {filtered.map((opt, i) => (
            <button
              key={i}
              type="button"
              onMouseDown={e => { e.preventDefault(); handleSelect(opt) }}
              className={cn(
                'flex w-full items-center gap-2 rounded-[7px] px-2.5 py-1.5 text-left text-[12px]',
                String(opt.value) === String(value) ? 'bg-surface-2 font-medium text-text' : 'text-text-mute hover:bg-surface hover:text-text',
              )}
            >
              <span className="flex-1 min-w-0">
                <span className="block">{opt.label}</span>
                {opt.description && <span className="block text-[10px] text-text-faint">{opt.description}</span>}
              </span>
              {String(opt.value) === String(value) && <Check size={11} className="shrink-0 text-accent" />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── MultiSelect (chips + checkbox dropdown) ───────────────────────────────────

interface MultiSelectProps {
  options: NodePropertyOption[]
  value: unknown
  onChange: (value: unknown) => void
  placeholder: string
  isLoading: boolean
  disabled?: boolean
}

function toArray(value: unknown): unknown[] {
  if (Array.isArray(value)) return value
  if (value === undefined || value === null || value === '') return []
  return [value]
}

function MultiSelect({ options, value, onChange, placeholder, isLoading, disabled }: MultiSelectProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const selected = toArray(value)

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const isPicked = (optValue: unknown) => selected.some(s => String(s) === String(optValue))

  const toggle = (optValue: unknown) => {
    onChange(isPicked(optValue)
      ? selected.filter(s => String(s) !== String(optValue))
      : [...selected, optValue])
  }

  const remove = (optValue: unknown) => {
    onChange(selected.filter(s => String(s) !== String(optValue)))
  }

  const selectedOptions = selected.map(v => options.find(o => String(o.value) === String(v)) ?? { label: String(v), value: v })

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        disabled={disabled}
        className={cn(
          'flex min-h-8 w-full items-center gap-1.5 rounded-[8px] border border-border-faint bg-bg p-1 pl-2 text-[12px] text-left',
          'transition-colors hover:border-border-soft',
          open && 'border-border bg-surface',
          disabled && 'opacity-50 cursor-not-allowed',
        )}
      >
        <div className="flex flex-1 min-w-0 flex-wrap items-center gap-1">
          {selectedOptions.length === 0 ? (
            <span className="text-text-faint">{isLoading ? 'Loading…' : placeholder}</span>
          ) : (
            selectedOptions.map((opt, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 rounded-[5px] bg-surface-2 px-1.5 py-0.5 text-[11px] text-text"
              >
                {opt.label}
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); remove(opt.value) }}
                  className="text-text-faint hover:text-err transition-colors"
                  aria-label={`Remove ${opt.label}`}
                >
                  <X size={10} />
                </button>
              </span>
            ))
          )}
        </div>
        {isLoading ? <Loader2 size={12} className="shrink-0 animate-spin text-text-faint" /> : <ChevronDown size={12} className={cn('shrink-0 text-text-faint transition-transform', open && 'rotate-180')} />}
      </button>

      {open && (
        <div className="absolute top-[calc(100%+4px)] left-0 right-0 z-50 max-h-52 overflow-y-auto rounded-[10px] border border-border-faint bg-bg p-1.5 shadow-dropdown">
          {options.length === 0 && (
            <p className="px-2.5 py-2 text-[11px] text-text-faint">No options</p>
          )}
          {options.map((opt, i) => {
            const picked = isPicked(opt.value)
            return (
              <button
                key={i}
                type="button"
                onClick={() => toggle(opt.value)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-[7px] px-2.5 py-1.5 text-left text-[12px]',
                  picked ? 'bg-surface-2 font-medium text-text' : 'text-text-mute hover:bg-surface hover:text-text',
                )}
              >
                <div className={cn(
                  'flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] border transition-colors',
                  picked ? 'border-[var(--accent)] bg-[var(--accent)] text-bg' : 'border-border-faint',
                )}>
                  {picked && <Check size={10} />}
                </div>
                <span className="flex-1 min-w-0">
                  <span className="block">{opt.label}</span>
                  {opt.description && <span className="block text-[10px] text-text-faint">{opt.description}</span>}
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

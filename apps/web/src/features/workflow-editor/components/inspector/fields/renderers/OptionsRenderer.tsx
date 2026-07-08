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

import { Select } from '@/components/ui/select'

interface SimpleSelectProps {
  options: NodePropertyOption[]
  value: unknown
  onChange: (value: unknown) => void
  placeholder: string
  isLoading: boolean
  disabled?: boolean
}

function SimpleSelect({ options, value, onChange, placeholder, isLoading, disabled }: SimpleSelectProps) {
  const formattedOptions = options.map(o => ({
    value: String(o.value),
    label: o.label,
    description: o.description,
  }))

  return (
    <Select
      options={formattedOptions}
      value={value !== undefined && value !== null ? String(value) : undefined}
      onChange={(val) => {
        const original = options.find(o => String(o.value) === val)
        onChange(original ? original.value : val)
      }}
      placeholder={isLoading ? 'Loading…' : placeholder}
      disabled={disabled || isLoading}
    />
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

  // Auto-focus the search input the moment we open.
  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  const filtered = query
    ? options.filter(o => o.label.toLowerCase().includes(query.toLowerCase()) || String(o.value).toLowerCase().includes(query.toLowerCase()))
    : options

  const handleSelect = (opt: NodePropertyOption) => {
    onChange(opt.value)
    setOpen(false)
    setQuery('')
  }

  const commitCustom = () => {
    const q = query.trim()
    if (!q) return
    onChange(q)
    setOpen(false)
    setQuery('')
  }

  return (
    <div ref={ref} className="relative">
      {/* Closed: static button showing the current label. Backspace on the
          trigger does nothing — selection is only changed via the dropdown.
          Opening reveals a search input above the list. */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        disabled={disabled}
        className={cn(
          'flex h-9 w-full items-center gap-2 rounded-[8px] border border-border-soft bg-surface px-3 text-sm text-left',
          'transition-[background-color,border-color] [transition-duration:120ms] hover:border-border hover:bg-surface-2',
          open && 'border-accent bg-surface-2',
          disabled && 'opacity-40 cursor-not-allowed',
        )}
      >
        <span className={cn('flex-1 min-w-0 truncate', !displayValue && 'text-text-faint')}>
          {isLoading ? 'Loading…' : (displayValue || placeholder)}
        </span>
        {isLoading ? <Loader2 className="shrink-0 w-3.5 h-3.5 animate-spin text-text-faint" /> : <ChevronDown className={cn('shrink-0 w-3.5 h-3.5 text-text-faint transition-transform [transition-duration:150ms]', open && 'rotate-180')} />}
      </button>

      {open && (
        <div className="absolute top-[calc(100%+4px)] left-0 right-0 z-50 rounded-[8px] border border-border-soft bg-surface shadow-dropdown animate-in fade-in-0 zoom-in-95 [transition-duration:100ms]">
          {/* Search input — pure filter, never mutates the value. */}
          <div className="border-b border-border-soft p-1.5">
            <input
              ref={inputRef}
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  if (filtered.length > 0) handleSelect(filtered[0])
                  else if (allowCustom) commitCustom()
                }
                if (e.key === 'Escape') { setOpen(false); setQuery('') }
              }}
              placeholder="Search…"
              spellCheck={false}
              className="h-8 w-full rounded-[6px] bg-surface px-2.5 text-sm text-text border border-border-soft outline-none focus:border-accent focus:bg-surface-2 placeholder:text-text-faint transition-[background-color,border-color] [transition-duration:120ms]"
            />
          </div>

          <div className="max-h-52 overflow-y-auto p-1.5">
            {filtered.length === 0 ? (
              allowCustom && query.trim() ? (
                <button
                  type="button"
                  onMouseDown={e => { e.preventDefault(); commitCustom() }}
                  className="flex w-full items-center gap-2 rounded-[6px] px-2.5 py-1.5 text-left text-sm text-text-mute hover:bg-surface hover:text-text transition-colors [transition-duration:100ms]"
                >
                  Use <span className="font-mono text-accent">{query.trim()}</span> as custom value
                </button>
              ) : (
                <p className="px-2.5 py-2 text-xs text-text-faint">No options</p>
              )
            ) : (
              filtered.map((opt, i) => (
                <button
                  key={i}
                  type="button"
                  onMouseDown={e => { e.preventDefault(); handleSelect(opt) }}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-[6px] px-2.5 py-1.5 text-left text-sm transition-colors [transition-duration:100ms]',
                    String(opt.value) === String(value) ? 'bg-surface-2 font-medium text-text' : 'text-text-mute hover:bg-surface hover:text-text',
                  )}
                >
                  <span className="flex-1 min-w-0">
                    <span className="block">{opt.label}</span>
                    {opt.description && <span className="block text-xs text-text-faint mt-px">{opt.description}</span>}
                  </span>
                  {String(opt.value) === String(value) && <Check className="shrink-0 w-3.5 h-3.5 text-accent" />}
                </button>
              ))
            )}
          </div>
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
          'flex min-h-[36px] w-full items-center gap-1.5 rounded-[8px] border border-border-soft bg-surface p-1.5 pl-3 text-sm text-left',
          'transition-[background-color,border-color] [transition-duration:120ms] hover:border-border hover:bg-surface-2',
          open && 'border-accent bg-surface-2',
          disabled && 'opacity-40 cursor-not-allowed',
        )}
      >
        <div className="flex flex-1 min-w-0 flex-wrap items-center gap-1">
          {selectedOptions.length === 0 ? (
            <span className="text-text-faint">{isLoading ? 'Loading…' : placeholder}</span>
          ) : (
            selectedOptions.map((opt, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-[6px] rounded-[6px] bg-surface px-2 py-0.5 text-xs text-text border border-border-soft"
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
        {isLoading ? <Loader2 className="shrink-0 w-3.5 h-3.5 animate-spin text-text-faint" /> : <ChevronDown className={cn('shrink-0 w-3.5 h-3.5 text-text-faint transition-transform [transition-duration:150ms]', open && 'rotate-180')} />}
      </button>

      {open && (
        <div className="absolute top-[calc(100%+4px)] left-0 right-0 z-50 max-h-52 overflow-y-auto rounded-[8px] border border-border-soft bg-surface p-1.5 shadow-dropdown animate-in fade-in-0 zoom-in-95 [transition-duration:100ms]">
          {options.length === 0 && (
            <p className="px-2.5 py-2 text-xs text-text-faint">No options</p>
          )}
          {options.map((opt, i) => {
            const picked = isPicked(opt.value)
            return (
              <button
                key={i}
                type="button"
                onClick={() => toggle(opt.value)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-[6px] px-2.5 py-1.5 text-left text-sm transition-colors [transition-duration:100ms]',
                  picked ? 'bg-surface-2 font-medium text-text' : 'text-text-mute hover:bg-surface hover:text-text',
                )}
              >
                <div className={cn(
                  'flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] border transition-colors',
                  picked ? 'border-accent bg-accent text-white' : 'border-border-soft bg-transparent',
                )}>
                  {picked && <Check size={10} />}
                </div>
                <span className="flex-1 min-w-0">
                  <span className="block">{opt.label}</span>
                  {opt.description && <span className="block text-xs text-text-faint mt-px">{opt.description}</span>}
                </span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

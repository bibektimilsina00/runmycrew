import { useState, useRef, useEffect } from 'react'
import { Check, ChevronDown, Loader2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import type { NodeProperty, NodePropertyOption } from '../../../../types/editorTypes'
import { useLoadOptions } from '../../hooks/use-load-options'

interface Props {
  prop: NodeProperty
  value: unknown
  onChange: (value: unknown) => void
  properties: Record<string, unknown>
}

export function OptionsRenderer({ prop, value, onChange, properties }: Props) {
  const { data: dynamicOptions = [], isLoading } = useLoadOptions(
    prop.loadOptions,
    prop.loadOptionsDependsOn,
    properties,
  )

  const allOptions: NodePropertyOption[] = [
    ...dynamicOptions,
    ...(prop.options ?? []),
  ]

  const allowCustom = prop.typeOptions?.allowCustom ?? false
  const searchable = prop.typeOptions?.searchable ?? false

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
}

function SimpleSelect({ options, value, onChange, placeholder, isLoading }: SimpleSelectProps) {
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
        className={cn(
          'flex h-8 w-full items-center gap-2 rounded-[8px] border border-border-faint bg-bg px-3 text-[12px] text-left',
          'transition-colors hover:border-border-soft',
          open && 'border-border bg-surface',
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
}

function ComboBox({ options, value, displayValue, onChange, placeholder, isLoading, allowCustom }: ComboBoxProps) {
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
          className={cn(
            'h-8 w-full rounded-[8px] border border-border-faint bg-bg pl-3 pr-8 text-[12px]',
            'placeholder:text-text-faint transition-colors',
            'focus:outline-none focus:border-border focus:bg-surface',
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

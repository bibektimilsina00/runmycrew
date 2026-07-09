import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import type { InputField, PublicApp } from '../types/publicAppTypes'

interface FormViewProps {
  app: PublicApp
  disabled?: boolean
  onSubmit: (values: Record<string, unknown>, summary: string) => void
}

/**
 * One-shot input page for form-mode apps. Renders each configured
 * ``input_field`` with the right control, validates required fields,
 * then hands the values to the parent which fires them as a
 * ``sendMessage`` (server unpacks into ``form_data``).
 */
export function FormView({ app, disabled, onSubmit }: FormViewProps) {
  const fields = app.config.input_fields ?? []
  const [values, setValues] = useState<Record<string, unknown>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})

  const set = (name: string, v: unknown) => setValues(prev => ({ ...prev, [name]: v }))

  const submit = () => {
    const errs: Record<string, string> = {}
    for (const f of fields) {
      if (f.required && !hasValue(values[f.name], f.type)) {
        errs[f.name] = 'Required'
      }
    }
    setErrors(errs)
    if (Object.keys(errs).length > 0) return
    const summaryParts: string[] = []
    for (const f of fields) {
      const v = values[f.name]
      if (hasValue(v, f.type)) summaryParts.push(`${f.label || f.name}: ${formatSummary(v)}`)
    }
    onSubmit(values, summaryParts.join('\n'))
  }

  return (
    <div className="mx-auto flex w-full max-w-[560px] flex-1 flex-col gap-5 px-4 py-8 sm:px-6">
      <header>
        <h1 className="text-[22px] font-semibold text-white">{app.title}</h1>
        {(app.description || app.config.welcome_sub) && (
          <p className="mt-1 text-[13.5px] leading-relaxed text-white/60">
            {app.config.welcome_sub || app.description}
          </p>
        )}
      </header>

      <form
        className="flex flex-col gap-4"
        onSubmit={e => {
          e.preventDefault()
          submit()
        }}
      >
        {fields.map(f => (
          <Field key={f.name} field={f} value={values[f.name]} error={errors[f.name]} onChange={v => set(f.name, v)} />
        ))}

        <button
          type="submit"
          disabled={disabled}
          className="mt-2 flex h-11 items-center justify-center gap-2 rounded-[10px] text-[14px] font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          style={{ background: 'var(--app-accent, #8b5cf6)' }}
        >
          {disabled ? <Loader2 size={14} className="animate-spin" /> : 'Run'}
        </button>
      </form>
    </div>
  )
}

function hasValue(v: unknown, type: string): boolean {
  if (v === null || v === undefined || v === '') return false
  if (type === 'boolean') return true // false is a valid answer
  if (Array.isArray(v)) return v.length > 0
  return true
}

function formatSummary(v: unknown): string {
  if (Array.isArray(v)) return v.join(', ')
  if (typeof v === 'object' && v !== null) return JSON.stringify(v)
  return String(v)
}

function Field({
  field,
  value,
  error,
  onChange,
}: {
  field: InputField
  value: unknown
  error?: string
  onChange: (v: unknown) => void
}) {
  const id = `field-${field.name}`
  const label = (
    <label htmlFor={id} className="text-[11px] font-medium uppercase tracking-wider text-white/60">
      {field.label || field.name}
      {field.required && <span className="ml-1 text-red-400/80">*</span>}
    </label>
  )
  const control = renderControl(field, id, value, onChange)
  return (
    <div className="flex flex-col gap-1.5">
      {label}
      {control}
      {field.help_text && <p className="text-[11px] text-white/40">{field.help_text}</p>}
      {error && <p className="text-[11px] text-red-400/80">{error}</p>}
    </div>
  )
}

function renderControl(
  field: InputField,
  id: string,
  value: unknown,
  onChange: (v: unknown) => void,
): React.ReactElement {
  const inputBase =
    'h-10 w-full rounded-[9px] border border-white/10 bg-white/[0.03] px-3 text-[14px] text-white placeholder:text-white/30 focus:border-white/25 focus:outline-none'
  switch (field.type) {
    case 'textarea':
      return (
        <textarea
          id={id}
          rows={5}
          value={String(value ?? '')}
          onChange={e => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={inputBase.replace('h-10', 'min-h-[92px] py-2')}
        />
      )
    case 'number':
      return (
        <input
          id={id}
          type="number"
          value={value === undefined || value === null ? '' : Number(value)}
          onChange={e => onChange(e.target.value === '' ? null : Number(e.target.value))}
          placeholder={field.placeholder}
          className={inputBase}
        />
      )
    case 'boolean':
      return (
        <label className="flex cursor-pointer items-center gap-2 text-[13px] text-white/70">
          <input
            id={id}
            type="checkbox"
            checked={!!value}
            onChange={e => onChange(e.target.checked)}
            className="h-4 w-4"
          />
          Yes
        </label>
      )
    case 'date':
      return (
        <input
          id={id}
          type="date"
          value={String(value ?? '')}
          onChange={e => onChange(e.target.value)}
          className={inputBase}
        />
      )
    case 'email':
      return (
        <input
          id={id}
          type="email"
          value={String(value ?? '')}
          onChange={e => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={inputBase}
        />
      )
    case 'url':
      return (
        <input
          id={id}
          type="url"
          value={String(value ?? '')}
          onChange={e => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={inputBase}
        />
      )
    default:
      return (
        <input
          id={id}
          type="text"
          value={String(value ?? '')}
          onChange={e => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={inputBase}
        />
      )
  }
}

import { useState } from 'react'
import { createPortal } from 'react-dom'
import { X, Play, Loader2 } from 'lucide-react'
import type { Node } from 'reactflow'

/**
 * Run dialog for a `trigger.form` workflow. The form node carries a typed
 * `inputs` schema (name + type + default); this renders one field per row,
 * collects the values, coerces them to the declared type, and hands them
 * back as `input_data` for a single run. Unlike Chat App, a form is NOT a
 * hosted public page — Run just opens this dialog and waits for input.
 */

type FormInput = { name?: string; type?: string; value?: unknown; label?: string }

const emptyFor = (type?: string): unknown =>
  type === 'boolean' ? false : type === 'number' ? '' : type === 'array' ? '' : type === 'object' ? '' : ''

function coerce(type: string | undefined, raw: unknown): unknown {
  if (type === 'number') return raw === '' || raw == null ? null : Number(raw)
  if (type === 'boolean') return Boolean(raw)
  if (type === 'object' || type === 'array') {
    if (typeof raw !== 'string' || raw.trim() === '') return type === 'array' ? [] : {}
    try {
      return JSON.parse(raw)
    } catch {
      return raw // leave as-is; backend surfaces the parse error
    }
  }
  return raw ?? ''
}

export function FormRunDialog({
  formNode,
  onRun,
  onClose,
  isRunning,
}: {
  formNode: Node
  onRun: (inputData: Record<string, unknown>) => void
  onClose: () => void
  isRunning: boolean
}) {
  const props = (formNode.data?.properties ?? {}) as Record<string, unknown>
  const inputs = (Array.isArray(props.inputs) ? props.inputs : []) as FormInput[]
  const title = (props.title as string) || (formNode.data?.label as string) || 'Run form'

  const [values, setValues] = useState<Record<string, unknown>>(() =>
    Object.fromEntries(inputs.map((i) => [i.name ?? '', i.value ?? emptyFor(i.type)])),
  )

  const set = (name: string, v: unknown) => setValues((s) => ({ ...s, [name]: v }))

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isRunning) return
    const inputData: Record<string, unknown> = {}
    for (const i of inputs) {
      if (!i.name) continue
      inputData[i.name] = coerce(i.type, values[i.name])
    }
    onRun(inputData)
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={submit}
        className="w-full max-w-[440px] rounded-[14px] border border-[var(--border)] bg-[var(--bg-2)] shadow-[0_24px_56px_-20px_rgba(0,0,0,0.7)]"
      >
        <div className="flex items-center gap-2 border-b border-[var(--border-faint)] px-[18px] py-[14px]">
          <span className="text-[14px] font-semibold text-[var(--text)]">{title}</span>
          <button
            type="button"
            onClick={onClose}
            className="ml-auto inline-flex h-[26px] w-[26px] items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
          >
            <X className="h-[15px] w-[15px]" />
          </button>
        </div>

        <div className="flex max-h-[60vh] flex-col gap-[14px] overflow-y-auto px-[18px] py-[16px]">
          {inputs.length === 0 && (
            <p className="text-[13px] text-[var(--text-mute)]">
              This form has no fields. Running will start the workflow with an empty input.
            </p>
          )}
          {inputs.map((i, idx) => {
            const name = i.name ?? `field_${idx}`
            const label = i.label || name
            const type = i.type ?? 'string'
            const val = values[name]
            return (
              <div key={name} className="flex flex-col gap-[6px]">
                <label htmlFor={name} className="text-[12.5px] font-medium text-[var(--text)]">
                  {label}
                  <span className="ml-[6px] font-mono text-[10.5px] text-[var(--text-dim)]">{type}</span>
                </label>
                {type === 'boolean' ? (
                  <label className="inline-flex items-center gap-[8px] text-[13px] text-[var(--text-mute)]">
                    <input
                      id={name}
                      type="checkbox"
                      checked={Boolean(val)}
                      onChange={(e) => set(name, e.target.checked)}
                      className="h-[15px] w-[15px] accent-[var(--accent)]"
                    />
                    {val ? 'true' : 'false'}
                  </label>
                ) : type === 'object' || type === 'array' ? (
                  <textarea
                    id={name}
                    rows={3}
                    value={String(val ?? '')}
                    onChange={(e) => set(name, e.target.value)}
                    placeholder={type === 'array' ? '[]' : '{}'}
                    className="w-full resize-none rounded-[8px] border border-[var(--border-soft)] bg-[var(--bg)] px-[10px] py-[8px] font-mono text-[12.5px] text-[var(--text)] outline-none transition-colors placeholder:text-[var(--text-dim)] focus:border-[var(--accent-line)]"
                  />
                ) : (
                  <input
                    id={name}
                    type={type === 'number' ? 'number' : 'text'}
                    value={String(val ?? '')}
                    onChange={(e) => set(name, e.target.value)}
                    className="h-[34px] w-full rounded-[8px] border border-[var(--border-soft)] bg-[var(--bg)] px-[10px] text-[13px] text-[var(--text)] outline-none transition-colors placeholder:text-[var(--text-dim)] focus:border-[var(--accent-line)]"
                  />
                )}
              </div>
            )
          })}
        </div>

        <div className="flex items-center justify-end gap-[8px] border-t border-[var(--border-faint)] px-[18px] py-[12px]">
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-[32px] items-center rounded-[8px] px-[12px] text-[12.5px] font-medium text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isRunning}
            className="inline-flex h-[32px] items-center gap-[6px] rounded-[8px] bg-[var(--accent)] px-[14px] text-[12.5px] font-semibold text-white transition-[filter] hover:brightness-110 disabled:opacity-60"
          >
            {isRunning ? <Loader2 className="h-[14px] w-[14px] animate-spin" /> : <Play className="h-[13px] w-[13px]" />}
            Run
          </button>
        </div>
      </form>
    </div>,
    document.body,
  )
}

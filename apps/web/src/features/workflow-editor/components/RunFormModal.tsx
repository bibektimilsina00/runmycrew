import { useMemo, useState } from 'react'
import { ClipboardList, Play, X } from 'lucide-react'
import type { Node } from 'reactflow'

interface FieldRow {
  name: string
  type: string
  value?: unknown
}

interface RunFormModalProps {
  /** The trigger.form node whose `inputs` schema drives the fields. */
  formNode: Node
  onSubmit: (values: Record<string, unknown>) => void
  onClose: () => void
}

/**
 * Run dialog for Form-trigger graphs: one control per configured field,
 * prefilled with the node's defaults. Submitted values ride the run as
 * `input_data` and override those defaults inside the trigger.
 */
export function RunFormModal({ formNode, onSubmit, onClose }: RunFormModalProps) {
  const fields = useMemo<FieldRow[]>(() => {
    const raw = (formNode.data?.properties as Record<string, unknown> | undefined)?.inputs
    if (!Array.isArray(raw)) return []
    return raw
      .filter((r): r is Record<string, unknown> => !!r && typeof r === 'object')
      .map((r, i) => ({
        name: typeof r.name === 'string' && r.name.trim() ? r.name.trim() : `input${i + 1}`,
        type: typeof r.type === 'string' ? r.type : 'string',
        value: r.value,
      }))
  }, [formNode])

  const [values, setValues] = useState<Record<string, unknown>>(() =>
    Object.fromEntries(fields.map(f => [f.name, f.value ?? (f.type === 'boolean' ? false : '')])),
  )
  const set = (name: string, v: unknown) => setValues(prev => ({ ...prev, [name]: v }))

  const submit = () => {
    const out: Record<string, unknown> = {}
    for (const f of fields) {
      const v = values[f.name]
      if (f.type === 'number') {
        const n = Number(v)
        out[f.name] = v === '' || v === null || Number.isNaN(n) ? null : n
      } else if (f.type === 'boolean') {
        out[f.name] = Boolean(v)
      } else if (f.type === 'object' || f.type === 'array' || f.type === 'json') {
        try {
          out[f.name] = typeof v === 'string' && v.trim() ? JSON.parse(v) : v
        } catch {
          out[f.name] = v // let the trigger's coercer take a swing
        }
      } else {
        out[f.name] = v ?? ''
      }
    }
    onSubmit(out)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-[2px]" onClick={onClose}>
      <div
        className="flex w-[440px] max-w-[92vw] flex-col overflow-hidden rounded-[14px] border border-[var(--border-faint)] bg-[var(--bg-2)] shadow-[0_24px_64px_-16px_rgba(0,0,0,0.7)]"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center gap-2.5 border-b border-[var(--border-faint)] px-4 py-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-[8px] bg-[var(--accent-soft)]">
            <ClipboardList className="h-3.5 w-3.5 text-[var(--accent)]" />
          </span>
          <div className="min-w-0 flex-1">
            <div className="text-[13.5px] font-semibold text-[var(--text)]">Run with form input</div>
            <div className="text-[11px] text-[var(--text-faint)]">
              Values are passed to the Form trigger and flow into the graph.
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-[6px] p-1 text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
            aria-label="Close"
          >
            <X size={14} />
          </button>
        </div>

        <form
          className="flex max-h-[60vh] flex-col gap-3.5 overflow-y-auto px-4 py-4"
          onSubmit={e => {
            e.preventDefault()
            submit()
          }}
        >
          {fields.length === 0 && (
            <p className="text-[12.5px] text-[var(--text-faint)]">
              This Form trigger has no fields yet — add some in its inspector, or just run.
            </p>
          )}
          {fields.map(f => (
            <label key={f.name} className="flex flex-col gap-1.5">
              <span className="text-[11.5px] font-medium text-[var(--text-mute)]">
                {f.name}
                <span className="ml-1.5 font-mono text-[10px] text-[var(--text-faint)]">{f.type}</span>
              </span>
              {f.type === 'boolean' ? (
                <input
                  type="checkbox"
                  checked={Boolean(values[f.name])}
                  onChange={e => set(f.name, e.target.checked)}
                  className="h-4 w-4"
                />
              ) : f.type === 'object' || f.type === 'array' || f.type === 'json' ? (
                <textarea
                  rows={3}
                  value={typeof values[f.name] === 'string' ? (values[f.name] as string) : JSON.stringify(values[f.name] ?? (f.type === 'array' ? [] : {}), null, 2)}
                  onChange={e => set(f.name, e.target.value)}
                  spellCheck={false}
                  className="rounded-[9px] border border-[var(--border-faint)] bg-[var(--bg)] px-3 py-2 font-mono text-[12px] text-[var(--text)] outline-none focus:border-[var(--border)]"
                />
              ) : (
                <input
                  type={f.type === 'number' ? 'number' : 'text'}
                  value={String(values[f.name] ?? '')}
                  onChange={e => set(f.name, e.target.value)}
                  className="h-9 rounded-[9px] border border-[var(--border-faint)] bg-[var(--bg)] px-3 text-[13px] text-[var(--text)] outline-none focus:border-[var(--border)]"
                />
              )}
            </label>
          ))}

          <button
            type="submit"
            className="mt-1 flex h-9 items-center justify-center gap-2 rounded-[9px] bg-[var(--accent)] text-[13px] font-semibold text-white transition-all hover:brightness-110"
          >
            <Play size={13} className="fill-current" />
            Run
          </button>
        </form>
      </div>
    </div>
  )
}

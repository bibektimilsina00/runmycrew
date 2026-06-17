import { useEffect, useRef, useState } from 'react'
import { Pencil } from 'lucide-react'
import type { NodeDefinition } from '../../../types/editorTypes'
import { getIcon } from '../../../utils/icon-map'

interface InspectorHeaderProps {
  label: string
  definition: NodeDefinition
  /** Returns the user-facing error string when the new label is rejected
   *  (empty or duplicate), or `null` when the rename was applied. */
  onLabelChange: (label: string) => string | null
}

export function InspectorHeader({ label, definition, onLabelChange }: InspectorHeaderProps) {
  const Icon = getIcon(definition.icon)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(label)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Effect-based focus: deterministic across React batching, no setTimeout race.
  useEffect(() => {
    if (editing) inputRef.current?.select()
  }, [editing])

  const startEdit = () => {
    setDraft(label)
    setError(null)
    setEditing(true)
  }

  const commit = () => {
    const trimmed = draft.trim()
    if (!trimmed || trimmed === label) {
      setEditing(false)
      setError(null)
      return
    }
    const rejection = onLabelChange(trimmed)
    if (rejection) {
      // Keep the editor open so the user can fix the input. Surface the reason
      // inline rather than via toast so it can't be missed.
      setError(rejection)
      return
    }
    setEditing(false)
    setError(null)
  }

  const category = definition.category
    ? definition.category.charAt(0).toUpperCase() + definition.category.slice(1)
    : 'Node'
  const subtitle = `${category} · ${definition.name}`

  return (
    <header className="shrink-0 border-b border-[var(--border-soft)] px-4 py-4">
      <div className="flex items-center gap-[11px]">
        <div
          className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[8px] text-white [&_svg]:h-[18px] [&_svg]:w-[18px]"
          style={{ background: definition.color ?? 'var(--surface-3)' }}
        >
          {Icon}
        </div>

        <div className="min-w-0 flex-1 leading-[1.3]">
          {editing ? (
            <input
              ref={inputRef}
              value={draft}
              onChange={e => {
                setDraft(e.target.value)
                if (error) setError(null)
              }}
              onBlur={commit}
              onKeyDown={e => {
                if (e.key === 'Enter') commit()
                if (e.key === 'Escape') {
                  setEditing(false)
                  setError(null)
                }
              }}
              className="w-full bg-transparent text-[14px] font-semibold text-[var(--text)] outline-none"
              aria-label="Node name"
              aria-invalid={!!error}
            />
          ) : (
            <span className="block truncate text-[14px] font-semibold text-[var(--text)]">
              {label}
            </span>
          )}
          <span className="block truncate text-[11.5px] text-[var(--text-faint)] font-medium">
            {subtitle}
          </span>
        </div>

        <button
          onClick={startEdit}
          className="flex h-[28px] w-[28px] shrink-0 items-center justify-center rounded-[6px] text-[var(--text-faint)] transition-colors hover:bg-[rgba(255,255,255,0.06)] hover:text-[var(--text)]"
          title="Rename node"
        >
          <Pencil className="h-[14px] w-[14px]" strokeWidth={1.8} />
        </button>
      </div>

      {error && (
        <p
          role="alert"
          className="mt-1.5 text-[11px] text-[var(--err)]"
        >
          {error}
        </p>
      )}
    </header>
  )
}

import { useRef, useState } from 'react'
import { Pencil, BookOpen } from 'lucide-react'
import type { NodeDefinition } from '../../../types/editorTypes'
import { getIcon } from '../../../utils/icon-map'

interface InspectorHeaderProps {
  nodeId: string
  label: string
  definition: NodeDefinition
  onLabelChange: (label: string) => void
  onClose: () => void
}

export function InspectorHeader({ label, definition, onLabelChange }: InspectorHeaderProps) {
  const Icon = getIcon(definition.icon)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(label)
  const inputRef = useRef<HTMLInputElement>(null)

  const startEdit = () => {
    setDraft(label)
    setEditing(true)
    setTimeout(() => inputRef.current?.select(), 0)
  }

  const commit = () => {
    const trimmed = draft.trim()
    if (trimmed && trimmed !== label) onLabelChange(trimmed)
    setEditing(false)
  }

  return (
    <header className="shrink-0 border-b border-[var(--border-faint)] px-4 py-3">
      <div className="flex items-center gap-2.5">
        <div
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[7px] text-white [&_svg]:h-3.5 [&_svg]:w-3.5"
          style={{ background: definition.color ?? 'var(--surface-3)' }}
        >
          {Icon}
        </div>

        <div className="min-w-0 flex-1">
          {editing ? (
            <input
              ref={inputRef}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onBlur={commit}
              onKeyDown={e => {
                if (e.key === 'Enter') commit()
                if (e.key === 'Escape') { setEditing(false) }
              }}
              className="w-full bg-transparent text-[13px] font-medium text-[var(--text)] outline-none"
              aria-label="Node name"
            />
          ) : (
            <span className="block truncate text-[13px] font-medium text-[var(--text)]">
              {label}
            </span>
          )}
        </div>

        <button
          onClick={startEdit}
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text-mute)]"
          title="Rename node"
        >
          <Pencil className="h-3 w-3" />
        </button>

        <button
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text-mute)]"
          title="View docs"
        >
          <BookOpen className="h-3 w-3" />
        </button>
      </div>
    </header>
  )
}

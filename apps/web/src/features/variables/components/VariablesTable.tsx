import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm, Empty } from '@/shared/components'
import { useRevealVariable, useUpdateVariable, useDeleteVariable } from '../hooks/useVariables'
import type { Variable, VariableScope } from '../types/variablesTypes'

interface Props {
  items: Variable[]
  totalCount?: number
}

const SCOPE_PILL: Record<string, string> = {
  workspace: 'bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]',
  personal:  'bg-[oklch(0.78_0.13_245/0.14)] text-[var(--accent)]',
}

export function VariablesTable({ items, totalCount = 0 }: Props) {
  const reveal = useRevealVariable()
  const update = useUpdateVariable()
  const remove = useDeleteVariable()
  const { toast } = useToast()
  const confirm = useConfirm()

  const [revealed, setRevealed] = useState<Record<string, string>>({})
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  const toggleReveal = async (v: Variable) => {
    if (revealed[v.id]) {
      setRevealed(r => { const n = { ...r }; delete n[v.id]; return n })
      return
    }
    const res = await reveal.mutateAsync(v.id)
    setRevealed(r => ({ ...r, [v.id]: res.value }))
  }

  const startEdit = (v: Variable) => {
    setEditingId(v.id)
    setEditValue(revealed[v.id] ?? v.value ?? '')
  }

  const saveEdit = async (v: Variable) => {
    const original = revealed[v.id] ?? v.value ?? ''
    if (editValue !== original) {
      await update.mutateAsync({ id: v.id, data: { value: editValue } })
      setRevealed(r => { const n = { ...r }; delete n[v.id]; return n })
      toast('Value updated', { variant: 'ok', description: `${v.name} has been updated.` })
    }
    setEditingId(null)
  }

  const handleDelete = async (id: string, name: string) => {
    const ok = await confirm({
      title: 'Delete variable',
      message: `Delete "${name}"? This cannot be undone.`,
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (!ok) return
    remove.mutate(id, {
      onSuccess: () => toast('Variable deleted', { variant: 'ok', description: `${name} has been removed.` }),
      onError: (err) => toast('Delete failed', { variant: 'err', description: err instanceof Error ? err.message : 'Try again.' }),
    })
    setRevealed(r => { const n = { ...r }; delete n[id]; return n })
  }

  const handleScopeChange = (id: string, scope: VariableScope) =>
    update.mutate({ id, data: { scope } }, {
      onSuccess: () => toast('Scope updated', { variant: 'ok' }),
    })

  return (
    <div className="panel">
      <div className="table table-vars">
        <div className="table-head">
          <span>Key</span>
          <span>Value</span>
          <span>Scope</span>
          <span>Updated</span>
          <span></span>
        </div>

        {items.length === 0 ? (
          <div
            className="flex-1 border-t border-[var(--border-faint)] flex items-center justify-center"
            style={{ minHeight: '400px', display: 'flex', flexDirection: 'column' }}
          >
            <Empty
              icon={<Icons.Key />}
              title="No variables found"
              description={
                totalCount === 0
                  ? "Define variables or secrets to use them in your automation workflows."
                  : "No variables match the current search query or filter tab."
              }
              className="py-10"
            />
          </div>
        ) : (
          items.map(v => {
            const isRevealed   = !!revealed[v.id]
            const displayVal   = revealed[v.id] ?? v.value ?? ''
            const maskedVal    = v.is_secret && !isRevealed ? '••••••••••••' : displayVal
            const isEditing    = editingId === v.id

            return (
              <div key={v.id} className="table-row group">
                {/* Key */}
                <span className="row-name mono">{v.name}</span>

                {/* Value */}
                <span className="var-val">
                  {isEditing ? (
                    <input
                      autoFocus
                      type={v.is_secret ? 'password' : 'text'}
                      value={editValue}
                      onChange={e => setEditValue(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') saveEdit(v); if (e.key === 'Escape') setEditingId(null) }}
                      className="flex-1 min-w-0 bg-[var(--bg)] border border-[var(--border)] rounded-[6px] px-2 py-1 text-[12px] font-mono text-[var(--text)] outline-none"
                    />
                  ) : (
                    <span className="font-mono text-[12px] text-[var(--text-mute)] truncate">
                      {maskedVal || <span className="text-[var(--text-dim)] italic not-italic">empty</span>}
                    </span>
                  )}

                  {/* Reveal toggle */}
                  {v.is_secret && !isEditing && (
                    <button
                      className="reveal-btn"
                      onClick={() => toggleReveal(v)}
                      title={isRevealed ? 'Hide' : 'Reveal'}
                      disabled={reveal.isPending}
                    >
                      {isRevealed ? <Icons.EyeOff /> : <Icons.Eye />}
                    </button>
                  )}

                  {/* Edit / Save */}
                  {isEditing ? (
                    <button
                      onClick={() => saveEdit(v)}
                      disabled={update.isPending}
                      className="shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-[5px] text-[11.5px] font-medium bg-[var(--text)] text-[var(--bg)] hover:opacity-80 transition-opacity"
                    >
                      {update.isPending ? '…' : 'Save'}
                    </button>
                  ) : (
                    <button
                      onClick={() => startEdit(v)}
                      title="Edit value"
                      className="reveal-btn opacity-0 group-hover:opacity-100"
                    >
                      <Icons.Edit style={{ width: 12, height: 12 }} />
                    </button>
                  )}
                </span>

                {/* Scope — inline select, no OS chrome */}
                <span>
                  <button
                    className={`font-mono text-[10px] tracking-widest uppercase px-[7px] py-[3px] pb-[2px] rounded-[4px] font-semibold border-none cursor-pointer transition-opacity hover:opacity-70 ${SCOPE_PILL[v.scope] ?? SCOPE_PILL.shared}`}
                    onClick={() => {
                      const next: VariableScope[] = ['workspace', 'personal']
                      const idx = next.indexOf(v.scope as VariableScope)
                      handleScopeChange(v.id, next[(idx + 1) % next.length])
                    }}
                    title="Click to change scope"
                  >
                    {v.scope}
                  </button>
                </span>

                {/* Updated */}
                <span className="row-mono">
                  {new Date(v.updated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>

                {/* Delete */}
                <span className="flex items-center justify-end">
                  <button
                    onClick={() => handleDelete(v.id, v.name)}
                    disabled={remove.isPending}
                    title="Delete variable"
                    className="w-[22px] h-[22px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)] transition-all"
                  >
                    <Icons.Trash style={{ width: 12, height: 12 }} />
                  </button>
                </span>
              </div>
            )
          })
        )
}

      </div>
    </div>
  )
}

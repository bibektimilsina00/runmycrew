import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useToast } from '@/shared/components'
import { useVariables, useCreateVariable } from '../hooks/useVariables'
import { VariablesTable } from '../components/VariablesTable'
import type { VariableScope } from '../types/variablesTypes'

const SCOPES: VariableScope[] = ['workspace', 'personal']

export function Variables() {
  const { data: items = [], isLoading } = useVariables()
  const createVar = useCreateVariable()
  const { toast } = useToast()

  const [filter, setFilter] = useState<'all' | 'secret' | 'plain' | 'workspace' | 'personal'>('all')
  const [search, setSearch] = useState('')

  // New variable form
  const [showForm, setShowForm] = useState(false)
  const [newName, setNewName]     = useState('')
  const [newVal, setNewVal]     = useState('')
  const [newScope, setNewScope] = useState<VariableScope>('workspace')
  const [newIsSecret, setNewIsSecret] = useState(true)
  const [formError, setFormError] = useState<string | null>(null)

  const filtered = items.filter(v => {
    if (filter === 'secret' && !v.is_secret) return false
    if (filter === 'plain'  &&  v.is_secret) return false
    if (filter === 'workspace' && v.scope !== 'workspace') return false
    if (filter === 'personal'  && v.scope !== 'personal')  return false
    if (search.trim() && !v.name.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const counts = {
    all: items.length,
    secret: items.filter(v => v.is_secret).length,
    plain:  items.filter(v => !v.is_secret).length,
    workspace: items.filter(v => v.scope === 'workspace').length,
    personal:  items.filter(v => v.scope === 'personal').length,
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    if (!newName.trim()) { setFormError('Key is required.'); return }
    try {
      await createVar.mutateAsync({ name: newName, value: newVal, scope: newScope, is_secret: newIsSecret })
      setNewName(''); setNewVal(''); setNewScope('workspace'); setNewIsSecret(true)
      setShowForm(false)
      toast('Variable created', { variant: 'ok', description: `${newName.toUpperCase().replace(/\s/g, '_')} added to ${newScope} scope.` })
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create variable.')
    }
  }

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · {items.length} variables · {counts.secret} secrets</span>
          <h1>Variables</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={() => {
            const rows = items.map(v => `${v.name},${v.is_secret ? '***' : (v.value ?? '')},${v.scope}`)
            const csv = ['name,value,scope', ...rows].join('\n')
            const a = document.createElement('a')
            a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
            a.download = 'variables.csv'
            a.click()
            toast('Exported', { variant: 'ok', description: `${items.length} variable${items.length !== 1 ? 's' : ''} exported to variables.csv` })
          }}>
            <Icons.Download /> Export
          </button>
          <button className="btn btn-primary" onClick={() => setShowForm(v => !v)}>
            <Icons.Plus /> New variable
          </button>
        </div>
      </div>

      {/* New variable form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="flex flex-col gap-4 p-5 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px]"
        >
          <div className="text-[13.5px] font-semibold text-[var(--text)]">New variable</div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[11.5px] font-medium text-[var(--text-mute)]">Key</label>
              <div className="flex items-center gap-2 px-3 h-[38px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] focus-within:border-[var(--border)] transition-colors">
                <Icons.Key style={{ width: 13, height: 13, color: 'var(--text-faint)', flexShrink: 0 }} />
                <input
                  type="text"
                  value={newName}
                  onChange={e => setNewName(e.target.value.toUpperCase().replace(/\s/g, '_'))}
                  placeholder="VARIABLE_NAME"
                  className="flex-1 bg-transparent border-none outline-none text-[13px] font-mono text-[var(--text)] placeholder:text-[var(--text-faint)]"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[11.5px] font-medium text-[var(--text-mute)]">Value</label>
              <div className="flex items-center gap-2 px-3 h-[38px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] focus-within:border-[var(--border)] transition-colors">
                <input
                  type={newIsSecret ? 'password' : 'text'}
                  value={newVal}
                  onChange={e => setNewVal(e.target.value)}
                  placeholder={newIsSecret ? '••••••••' : 'value'}
                  className="flex-1 bg-transparent border-none outline-none text-[13px] font-mono text-[var(--text)] placeholder:text-[var(--text-faint)]"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-5 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-[12px] text-[var(--text-mute)]">Scope:</span>
              <div className="flex items-center bg-[var(--surface)] border border-[var(--border-faint)] rounded-[7px] p-[2px] gap-[2px]">
                {SCOPES.map(s => (
                  <button
                    key={s} type="button"
                    onClick={() => setNewScope(s)}
                    className={`px-3 py-1 rounded-[5px] text-[11.5px] font-medium capitalize transition-colors ${newScope === s ? 'bg-[var(--bg-2)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]' : 'text-[var(--text-mute)] hover:text-[var(--text)]'}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <div
                onClick={() => setNewIsSecret(v => !v)}
                className={`w-[36px] h-[20px] rounded-full relative transition-colors cursor-pointer ${newIsSecret ? 'bg-[var(--text)]' : 'bg-[var(--surface-3)]'}`}
              >
                <span className={`absolute top-[2px] w-[16px] h-[16px] rounded-full bg-[var(--bg)] transition-transform ${newIsSecret ? 'translate-x-[18px]' : 'translate-x-[2px]'}`} />
              </div>
              <span className="text-[12px] text-[var(--text-mute)]">Secret</span>
            </label>
          </div>

          {formError && <p className="text-[12px] text-[var(--err)]">{formError}</p>}

          <div className="flex items-center justify-end gap-3">
            <button type="button" onClick={() => { setShowForm(false); setFormError(null) }}
              className="px-4 py-2 rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={createVar.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors disabled:opacity-50">
              <Icons.Plus style={{ width: 13, height: 13 }} />
              {createVar.isPending ? 'Creating…' : 'Create variable'}
            </button>
          </div>
        </form>
      )}

      {/* Filter bar */}
      <div className="filter-bar">
        <div className="filter-tabs">
          {([
            ['all', 'All'],
            ['secret', 'Secrets'],
            ['plain', 'Plain'],
            ['workspace', 'Workspace'],
            ['personal', 'Personal'],
          ] as const).map(([id, label]) => (
            counts[id] > 0 || id === 'all' ? (
              <button key={id} className={`filter-tab${filter === id ? ' active' : ''}`} onClick={() => setFilter(id)}>
                {label} <span className="filter-count">{counts[id]}</span>
              </button>
            ) : null
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input
              placeholder="Filter by key"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
          <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
          Loading variables…
        </div>
      ) : (
        <VariablesTable items={filtered} totalCount={items.length} />
      )}
    </div>
  )
}

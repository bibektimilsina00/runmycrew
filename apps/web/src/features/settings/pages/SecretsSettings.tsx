import React, { useState, useEffect } from 'react'
import { Trash2, Plus, Eye, EyeOff, Copy, Check, Loader2 } from 'lucide-react'
import { SettingsPageContainer, SettingsPageHeader } from '@/features/settings/components/shared/SettingsLayout'
import apiClient from '@/lib/api/client'

interface Secret {
  id: string
  name: string
  created_at: string
  updated_at: string
}

export const SecretsSettings: React.FC = () => {
  const [secrets, setSecrets] = useState<Secret[]>([])
  const [loading, setLoading] = useState(true)
  const [newName, setNewName] = useState('')
  const [newValue, setNewValue] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showNew, setShowNew] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const res = await apiClient.get('/secrets/')
      setSecrets(res.data || [])
    } catch { }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleAdd = async () => {
    const name = newName.trim().toUpperCase().replace(/\s+/g, '_')
    const value = newValue.trim()
    if (!name || !value) return
    setAdding(true)
    setError(null)
    try {
      await apiClient.post('/secrets/', { name, value })
      setNewName('')
      setNewValue('')
      setShowNew(false)
      load()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to create secret')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this secret? Any workflow using {{secrets.NAME}} will stop working.')) return
    await apiClient.delete(`/secrets/${id}`)
    setSecrets(s => s.filter(x => x.id !== id))
  }

  const copyRef = (name: string) => {
    navigator.clipboard.writeText(`{{secrets.${name}}}`)
    setCopied(name)
    setTimeout(() => setCopied(null), 1500)
  }

  const filtered = search ? secrets.filter(s => s.name.toLowerCase().includes(search.toLowerCase())) : secrets

  return (
    <SettingsPageContainer>
      <SettingsPageHeader
        title="Secrets"
        description="Store sensitive values and reference them in any node with {{secrets.MY_KEY}}"
      />

      <div className="flex items-center gap-3 mb-6">
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search secrets..."
          className="flex-1 h-[36px] px-3 rounded-lg bg-[var(--surface-3)] border border-[var(--border-default)] text-[13px] text-white placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)]"
        />
        <button
          onClick={() => setShowNew(v => !v)}
          className="flex items-center gap-1.5 h-[36px] px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[13px] font-medium transition-colors"
        >
          <Plus className="w-3.5 h-3.5" /> New Secret
        </button>
      </div>

      {/* Add form */}
      {showNew && (
        <div className="mb-6 p-4 rounded-xl border border-[var(--border-default)] bg-[var(--surface-3)] flex flex-col gap-3">
          <p className="text-[12px] font-semibold text-white">Add Secret</p>
          <div className="flex gap-3">
            <input
              value={newName}
              onChange={e => setNewName(e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, '_'))}
              placeholder="SECRET_NAME"
              className="flex-1 h-[34px] px-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border-default)] text-[13px] text-white font-mono placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)]"
            />
            <div className="flex-[1.5] relative">
              <input
                type={showNew ? 'text' : 'password'}
                value={newValue}
                onChange={e => setNewValue(e.target.value)}
                placeholder="Value"
                className="w-full h-[34px] px-3 pr-9 rounded-lg bg-[var(--surface-2)] border border-[var(--border-default)] text-[13px] text-white placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)]"
              />
            </div>
          </div>
          {error && <p className="text-[12px] text-red-400">{error}</p>}
          <div className="flex gap-2 justify-end">
            <button onClick={() => { setShowNew(false); setError(null) }} className="px-3 py-1.5 text-[12px] text-[var(--text-muted)] hover:text-white transition-colors">Cancel</button>
            <button onClick={handleAdd} disabled={adding || !newName.trim() || !newValue.trim()} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[12px] font-medium transition-colors disabled:opacity-50">
              {adding ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />} Add
            </button>
          </div>
        </div>
      )}

      {/* Secrets list */}
      {loading ? (
        <div className="flex items-center gap-2 text-[var(--text-muted)] py-8">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading...
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center">
          <p className="text-[13px] text-[var(--text-muted)]">{search ? 'No secrets match your search' : 'No secrets yet. Add one to get started.'}</p>
          {!search && <p className="text-[12px] text-[var(--text-muted)] mt-1">Use <code className="bg-[var(--surface-3)] px-1 rounded text-indigo-400">{'{{secrets.MY_KEY}}'}</code> in any node property.</p>}
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {filtered.map(s => (
            <div key={s.id} className="flex items-center gap-3 px-4 py-3 rounded-xl border border-[var(--border-default)] bg-[var(--surface-3)] group">
              <span className="flex-1 text-[13px] text-white font-mono">{s.name}</span>
              <span className="text-[12px] text-[var(--text-muted)] font-mono tracking-wider">••••••••</span>
              <button
                onClick={() => copyRef(s.name)}
                className="p-1.5 rounded text-[var(--text-muted)] hover:text-white transition-colors opacity-0 group-hover:opacity-100"
                title={`Copy {{secrets.${s.name}}}`}
              >
                {copied === s.name ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={() => handleDelete(s.id)}
                className="p-1.5 rounded text-[var(--text-muted)] hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 p-4 rounded-xl border border-dashed border-[var(--border-default)] bg-[var(--surface-2)]">
        <p className="text-[12px] font-semibold text-white mb-2">How to use secrets</p>
        <p className="text-[12px] text-[var(--text-muted)] leading-relaxed">
          Reference any secret in node properties using <code className="bg-[var(--surface-3)] px-1 rounded text-indigo-400">{'{{secrets.SECRET_NAME}}'}</code>.
          Secret values are encrypted at rest and never exposed in logs or outputs.
        </p>
        <div className="mt-3 flex flex-col gap-1 text-[11px] text-[var(--text-muted)] font-mono">
          <span><span className="text-indigo-400">{'{{secrets.OPENAI_KEY}}'}</span> → sk-abc...</span>
          <span><span className="text-indigo-400">{'{{secrets.DB_PASSWORD}}'}</span> → supersecret</span>
        </div>
      </div>
    </SettingsPageContainer>
  )
}

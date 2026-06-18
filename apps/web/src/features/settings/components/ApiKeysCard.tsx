import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import type { ApiKey } from '../types/settingsTypes'

interface Props {
  apiKeys: ApiKey[]
  isGenerating: boolean
  onCreateKey: (name: string) => Promise<ApiKey>
  onRevokeKey: (id: string, name: string) => void
}

export function ApiKeysCard({ apiKeys, isGenerating, onCreateKey, onRevokeKey }: Props) {
  const [newKeyName, setNewKeyName] = useState('')

  const handleCreate = async () => {
    if (!newKeyName.trim()) return
    await onCreateKey(newKeyName.trim())
    setNewKeyName('')
  }

  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[var(--border-faint)]">
        <div className="flex items-center gap-2 text-[14px] font-semibold text-[var(--text)] tracking-tight">
          <Icons.Key className="w-[14px] h-[14px] text-[var(--text-faint)]" />
          Developer API keys
        </div>
        <p className="text-[12px] text-[var(--text-faint)] mt-1">Authenticate CLI agents and remote services.</p>
      </div>

      <div className="p-6 flex flex-col gap-5">
        {/* Create row */}
        <div className="flex gap-3">
          <div className="flex items-center gap-2.5 px-3 h-[38px] flex-1 bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] focus-within:border-[var(--border)] transition-colors">
            <Icons.Key className="w-[14px] h-[14px] text-[var(--text-faint)] shrink-0" />
            <input
              type="text"
              placeholder="Key description (e.g. Production daemon)"
              value={newKeyName}
              onChange={e => setNewKeyName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              disabled={isGenerating}
              className="flex-1 bg-transparent border-none outline-none text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] disabled:opacity-50"
            />
          </div>
          <button
            onClick={handleCreate}
            disabled={isGenerating || !newKeyName.trim()}
            className="inline-flex items-center gap-2 px-4 h-[38px] rounded-[9px] bg-[var(--accent)] text-white text-[13px] font-medium border-none cursor-pointer shrink-0 transition-colors hover:brightness-110 disabled:opacity-50 disabled:cursor-default"
          >
            <Icons.Plus className="w-[13px] h-[13px]" />
            {isGenerating ? 'Generating…' : 'Generate'}
          </button>
        </div>

        {/* Key list */}
        {apiKeys.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 border border-dashed border-[var(--border-faint)] rounded-[10px]">
            <Icons.Key className="w-[18px] h-[18px] text-[var(--text-dim)]" />
            <span className="text-[12.5px] text-[var(--text-faint)]">No API keys yet. Generate one above.</span>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {apiKeys.map(k => (
              <div
                key={k.id}
                className="flex items-center gap-4 px-4 py-3 bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[10px] hover:border-[var(--border-soft)] transition-colors group"
              >
                <div className="flex flex-col gap-1 flex-1 min-w-0">
                  <span className="text-[13px] font-medium text-[var(--text)] truncate">{k.name}</span>
                  <span className="font-mono text-[11px] text-[var(--text-faint)] bg-[var(--bg)] border border-[var(--border-faint)] px-2 py-0.5 rounded-[5px] w-fit select-all">
                    {k.key_preview}
                  </span>
                  <span className="text-[10.5px] text-[var(--text-dim)] font-mono mt-0.5">
                    Created {new Date(k.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                </div>
                <button
                  onClick={() => onRevokeKey(k.id, k.name)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[7px] text-[12px] font-medium text-[var(--text-dim)] bg-transparent border border-transparent hover:border-[oklch(0.70_0.18_22/0.3)] hover:text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.08)] transition-colors opacity-0 group-hover:opacity-100"
                  title="Revoke key"
                >
                  <Icons.Trash className="w-[12px] h-[12px]" />
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

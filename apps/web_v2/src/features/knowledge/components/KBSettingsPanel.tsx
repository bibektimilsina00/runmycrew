import { useState, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { Icons } from '@/shared/components/icons'
import { useToast } from '@/shared/components'
import {
  Dropdown, DropdownTrigger, DropdownContent, DropdownItem,
} from '@/shared/components/Dropdown'
import { knowledgeAPI } from '../services/knowledgeAPI'
import { useReindex } from '../hooks/useKnowledge'
import { useCredentials } from '@/features/connections/hooks/useConnections'
import { EMBEDDING_MODELS, CHUNKING_STRATEGIES } from '../types/knowledgeTypes'
import type { KBDetail } from '../types/knowledgeTypes'

interface Props {
  kb: KBDetail
  onClose: () => void
  onSaved: () => void
}

export function KBSettingsPanel({ kb, onClose, onSaved }: Props) {
  const { toast } = useToast()
  const { data: credentials = [] } = useCredentials()

  const [model, setModel]         = useState(kb.embedding_model || 'text-embedding-3-small')
  const [credId, setCredId]       = useState(kb.embedding_credential_id ?? '')
  const [minChunk, setMinChunk]   = useState(kb.min_chunk_size ?? 100)
  const [maxTokens, setMaxTokens] = useState(kb.max_chunk_tokens ?? 1024)
  const [overlap, setOverlap]     = useState(kb.overlap_tokens ?? 200)
  const [strategy, setStrategy]   = useState(kb.chunking_strategy ?? 'auto')
  const [saving, setSaving]       = useState(false)
  const [error, setError]         = useState<string | null>(null)
  const reindex = useReindex(kb.id)

  const selectedModel    = EMBEDDING_MODELS.find(m => m.id === model)
  const selectedStrategy = CHUNKING_STRATEGIES.find(s => s.id === strategy)

  const relevantCreds = useMemo(
    () => credentials.filter(c => c.type === selectedModel?.credType),
    [credentials, selectedModel?.credType]
  )
  const selectedCred = relevantCreds.find(c => c.id === credId)

  const handleModelChange = (modelId: string) => {
    setModel(modelId)
    const m = EMBEDDING_MODELS.find(x => x.id === modelId)
    if (m && !credentials.some(c => c.type === m.credType && c.id === credId)) setCredId('')
  }

  const handleSave = async () => {
    if (!credId) { setError(`Select a ${selectedModel?.provider} credential.`); return }
    setError(null); setSaving(true)
    try {
      await knowledgeAPI.update(kb.id, {
        name: kb.name,
        description: kb.description ?? undefined,
        embedding_model: model,
        embedding_credential_id: credId,
        min_chunk_size: minChunk,
        max_chunk_tokens: maxTokens,
        overlap_tokens: overlap,
        chunking_strategy: strategy,
      })
      toast('Settings saved', { variant: 'ok', description: 'Embedding model configured.' })
      // Auto re-index documents that failed to index (have no chunks but have raw content)
      if (kb.document_count > 0 && kb.total_chunks === 0) {
        try {
          const result = await reindex.mutateAsync()
          if (result.reindexed > 0) {
            toast('Re-indexing complete', { variant: 'ok', description: result.message })
          } else if (result.needs_reupload > 0) {
            toast('Re-upload needed', { variant: 'ok', description: result.message })
          }
        } catch { /* non-critical */ }
      }
      onSaved()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save.')
    } finally {
      setSaving(false)
    }
  }

  const modelsByProvider = useMemo(() =>
    ['OpenAI', 'Google', 'Mistral'].map(p => ({
      provider: p,
      models: EMBEDDING_MODELS.filter(m => m.provider === p),
    })), []
  )

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9997] bg-black/30 backdrop-blur-[2px]" onClick={onClose} />
      <div className="fixed top-0 right-0 bottom-0 z-[9998] w-full max-w-[420px] bg-[var(--bg-2)] border-l border-[var(--border-faint)] flex flex-col shadow-[-24px_0_48px_-20px_oklch(0_0_0/0.4)]">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-faint)] shrink-0">
          <div>
            <h3 className="text-[14px] font-semibold text-[var(--text)] tracking-tight">Settings</h3>
            <p className="text-[12px] text-[var(--text-faint)] mt-0.5">{kb.name}</p>
          </div>
          <button onClick={onClose} className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-6">

          {/* Embedding model — providers with no credential shown disabled */}
          <div className="flex flex-col gap-3">
            <div>
              <div className="text-[13px] font-semibold text-[var(--text)]">Embedding model</div>
              <p className="text-[12px] text-[var(--text-faint)] mt-0.5">Used to convert documents and queries into vectors for retrieval.</p>
            </div>
            <div className="flex flex-col gap-3">
              {modelsByProvider.map(({ provider, models }) => {
                const credType = EMBEDDING_MODELS.find(m => m.provider === provider)?.credType ?? ''
                const hasCred  = credentials.some(c => c.type === credType)
                return (
                  <div key={provider}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)]">{provider}</span>
                      {hasCred
                        ? <span className="inline-flex items-center gap-1 text-[10px] font-mono text-[var(--ok)]"><Icons.Check style={{ width: 10, height: 10 }} /> credential connected</span>
                        : <span className="text-[10px] font-mono text-[var(--warn)]">no credential — add in Connections</span>
                      }
                    </div>
                    <div className="flex flex-col gap-1.5">
                      {models.map(m => (
                        <label key={m.id}
                          onClick={() => hasCred && handleModelChange(m.id)}
                          className={`flex items-center gap-3 px-3 py-2.5 rounded-[9px] border transition-colors
                            ${!hasCred ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
                            ${model === m.id ? 'bg-[var(--surface)] border-[var(--border-soft)]' : hasCred ? 'bg-[var(--bg)] border-[var(--border-faint)] hover:border-[var(--border-soft)]' : 'bg-[var(--bg)] border-[var(--border-faint)]'}`
                          }>
                          <input type="radio" name="setting-model" value={m.id} checked={model === m.id} disabled={!hasCred} readOnly className="accent-[var(--text)]" />
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[13px] font-medium text-[var(--text)]">{m.label}</span>
                            <span className="text-[11px] font-mono text-[var(--text-faint)]">{m.dims.toLocaleString()} dims</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Credential — only shown for selected model's provider */}
          <div className="flex flex-col gap-2">
            <div className="text-[13px] font-semibold text-[var(--text)]">{selectedModel?.provider} credential</div>
            {relevantCreds.length === 0 ? (
              <div className="flex items-center gap-2 px-3 py-2.5 bg-[oklch(0.82_0.14_80/0.10)] border border-[oklch(0.82_0.14_80/0.3)] rounded-[9px]">
                <Icons.Activity style={{ width: 13, height: 13, color: 'var(--warn)' }} />
                <span className="text-[12px] text-[var(--warn)]">No {selectedModel?.provider} credentials. Add one in Connections.</span>
              </div>
            ) : (
              <Dropdown className="w-full">
                <DropdownTrigger className="w-full">
                  <div className="flex items-center justify-between h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] cursor-pointer hover:border-[var(--border-soft)] transition-colors">
                    <span className={selectedCred ? 'text-[var(--text)]' : 'text-[var(--text-faint)]'}>
                      {selectedCred?.name ?? `Select ${selectedModel?.provider} credential…`}
                    </span>
                    <Icons.Caret style={{ width: 11, height: 11, color: 'var(--text-faint)' }} />
                  </div>
                </DropdownTrigger>
                <DropdownContent className="w-full">
                  {relevantCreds.map(c => (
                    <DropdownItem key={c.id} onClick={() => setCredId(c.id)} className={credId === c.id ? 'bg-[var(--surface)]' : ''}>
                      <div className="flex items-center justify-between w-full">
                        <span>{c.name}</span>
                        {credId === c.id && <Icons.Check style={{ width: 13, height: 13, color: 'var(--ok)' }} />}
                      </div>
                    </DropdownItem>
                  ))}
                </DropdownContent>
              </Dropdown>
            )}
          </div>

          <div className="h-px bg-[var(--border-faint)]" />

          {/* Chunking */}
          <div className="flex flex-col gap-3">
            <div>
              <div className="text-[13px] font-semibold text-[var(--text)]">Chunking</div>
              <p className="text-[12px] text-[var(--text-faint)] mt-0.5">How documents are split into indexed pieces.</p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Min size', unit: 'chars', val: minChunk, set: setMinChunk, min: 50 },
                { label: 'Max size', unit: 'tokens', val: maxTokens, set: setMaxTokens, min: 128 },
                { label: 'Overlap', unit: 'tokens', val: overlap, set: setOverlap, min: 0 },
              ].map(f => (
                <div key={f.label} className="flex flex-col gap-1">
                  <span className="text-[11px] text-[var(--text-faint)]">{f.label}</span>
                  <div className="relative">
                    <input type="number" value={f.val} min={f.min} onChange={e => f.set(Math.max(f.min, Number(e.target.value)))}
                      className="w-full h-[34px] px-2 pr-12 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[8px] text-[12.5px] text-[var(--text)] outline-none focus:border-[var(--border)] transition-colors" />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] font-mono text-[var(--text-dim)] pointer-events-none">{f.unit}</span>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-[11px] font-mono text-[var(--text-dim)]">1 token ≈ 4 characters</p>

            <Dropdown className="w-full">
              <DropdownTrigger className="w-full">
                <div className="flex items-center justify-between h-[36px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[8px] text-[12.5px] text-[var(--text)] cursor-pointer hover:border-[var(--border-soft)] transition-colors">
                  <span>{selectedStrategy?.label ?? 'Auto'}</span>
                  <Icons.Caret style={{ width: 10, height: 10, color: 'var(--text-faint)' }} />
                </div>
              </DropdownTrigger>
              <DropdownContent className="w-full">
                {CHUNKING_STRATEGIES.map(s => (
                  <DropdownItem key={s.id} onClick={() => setStrategy(s.id)} className={strategy === s.id ? 'bg-[var(--surface)]' : ''}>
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[13px] font-medium">{s.label}</span>
                      <span className="text-[11px] text-[var(--text-faint)]">{s.desc}</span>
                    </div>
                  </DropdownItem>
                ))}
              </DropdownContent>
            </Dropdown>
          </div>

          {error && <p className="text-[12px] text-[var(--err)]">{error}</p>}
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-[var(--border-faint)] shrink-0 flex items-center justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !credId}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors disabled:opacity-40 disabled:cursor-default"
          >
            {saving ? 'Saving…' : 'Save settings'}
          </button>
        </div>
      </div>
    </>,
    document.body
  )
}

import { useState, useRef, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm } from '@/shared/components'
import {
  Dropdown, DropdownTrigger, DropdownContent, DropdownItem,
} from '@/shared/components/Dropdown'
import {
  useKBDetail, useAddTextDoc, useUploadDoc, useAddUrlDoc,
  useDeleteDoc, useKBSearch, useReindexDoc,
} from '../hooks/useKnowledge'
import { knowledgeAPI } from '../services/knowledgeAPI'
import { useCredentials } from '@/features/connections/hooks/useConnections'
import { EMBEDDING_MODELS, CHUNKING_STRATEGIES } from '../types/knowledgeTypes'
import type { KnowledgeBase, SearchResult } from '../types/knowledgeTypes'

type AddTab = 'text' | 'file' | 'url'

interface Props {
  kb: KnowledgeBase
  onClose: () => void
}


export function KBDetailPanel({ kb, onClose }: Props) {
  const { toast } = useToast()
  const confirm = useConfirm()
  const { data: detail, isLoading, refetch } = useKBDetail(kb.id)
  const { data: credentials = [] } = useCredentials()

  const addText   = useAddTextDoc(kb.id)
  const uploadDoc = useUploadDoc(kb.id)
  const addUrl    = useAddUrlDoc(kb.id)
  const deleteDoc = useDeleteDoc(kb.id)
  const reindexDoc = useReindexDoc(kb.id)
  const search    = useKBSearch(kb.id)

  const [panel, setPanel] = useState<'docs' | 'add' | 'search'>('docs')

  // ── Setup state (shown when KB has no embedding credential) ──
  const isConfigured = !!(detail?.embedding_credential_id ?? kb.embedding_credential_id)
  const [setupModel, setSetupModel]   = useState(kb.embedding_model || 'text-embedding-3-small')
  const [setupCredId, setSetupCredId] = useState(kb.embedding_credential_id ?? '')
  const [setupMinChunk, setSetupMinChunk]       = useState(kb.min_chunk_size ?? 100)
  const [setupMaxTokens, setSetupMaxTokens]     = useState(kb.max_chunk_tokens ?? 1024)
  const [setupOverlap, setSetupOverlap]         = useState(kb.overlap_tokens ?? 200)
  const [setupStrategy, setSetupStrategy]       = useState(kb.chunking_strategy ?? 'auto')
  const [setupSaving, setSetupSaving]           = useState(false)
  const [setupError, setSetupError]             = useState<string | null>(null)

  const selectedSetupModel = EMBEDDING_MODELS.find(m => m.id === setupModel)
  const relevantCreds = useMemo(
    () => credentials.filter(c => c.type === selectedSetupModel?.credType),
    [credentials, selectedSetupModel?.credType]
  )
  const selectedSetupCred = relevantCreds.find(c => c.id === setupCredId)
  const selectedSetupStrategy = CHUNKING_STRATEGIES.find(s => s.id === setupStrategy)

  const handleSaveSetup = async () => {
    if (!setupCredId) { setSetupError(`Select a ${selectedSetupModel?.provider} credential.`); return }
    setSetupError(null); setSetupSaving(true)
    try {
      await knowledgeAPI.update(kb.id, {
        name: kb.name,
        description: kb.description ?? undefined,
        embedding_model: setupModel,
        embedding_credential_id: setupCredId,
        min_chunk_size: setupMinChunk,
        max_chunk_tokens: setupMaxTokens,
        overlap_tokens: setupOverlap,
        chunking_strategy: setupStrategy,
      })
      await refetch()
      toast('Knowledge base configured', { variant: 'ok', description: 'Ready to add documents.' })
    } catch (err) {
      setSetupError(err instanceof Error ? err.message : 'Failed to save.')
    } finally {
      setSetupSaving(false)
    }
  }
  const [addTab, setAddTab] = useState<AddTab>('text')

  // Add text form
  const [textName, setTextName] = useState('')
  const [textBody, setTextBody] = useState('')

  // Add URL form
  const [urlValue, setUrlValue] = useState('')

  // Search
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])

  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleAddText = async () => {
    if (!textName.trim() || !textBody.trim()) return
    await addText.mutateAsync({ name: textName, text: textBody })
    toast('Document added', { variant: 'ok', description: `"${textName}" indexed.` })
    setTextName(''); setTextBody(''); setPanel('docs')
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    await uploadDoc.mutateAsync(file)
    toast('File uploaded', { variant: 'ok', description: `"${file.name}" indexed.` })
    setPanel('docs')
    e.target.value = ''
  }

  const handleAddUrl = async () => {
    if (!urlValue.trim()) return
    await addUrl.mutateAsync(urlValue.trim())
    toast('URL added', { variant: 'ok', description: 'Page content indexed.' })
    setUrlValue(''); setPanel('docs')
  }

  const handleDeleteDoc = async (docId: string, docName: string) => {
    const ok = await confirm({ title: 'Delete document', message: `Delete "${docName}"? Its chunks will be removed from the index.`, confirmText: 'Delete', variant: 'danger' })
    if (!ok) return
    await deleteDoc.mutateAsync(docId)
    toast('Document deleted', { variant: 'ok' })
  }

  const handleSearch = async () => {
    if (!query.trim()) return
    const res = await search.mutateAsync({ query })
    setResults(res.results)
  }

  const isBusy = addText.isPending || uploadDoc.isPending || addUrl.isPending

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9997] bg-black/30 backdrop-blur-[2px]" onClick={onClose} />
      <div className="fixed top-0 right-0 bottom-0 z-[9998] w-full max-w-[520px] bg-[var(--bg-2)] border-l border-[var(--border-faint)] flex flex-col shadow-[-24px_0_48px_-20px_oklch(0_0_0/0.4)]">

        {/* Header */}
        <div className="flex items-start justify-between px-6 py-4 border-b border-[var(--border-faint)] shrink-0">
          <div className="flex flex-col gap-0.5 min-w-0">
            <h3 className="text-[14px] font-semibold text-[var(--text)] tracking-tight truncate">{kb.name}</h3>
            <p className="text-[11.5px] font-mono text-[var(--text-faint)]">
              {detail?.total_chunks ?? kb.total_chunks} chunks · {kb.embedding_model}
            </p>
          </div>
          <button onClick={onClose} className="w-[28px] h-[28px] shrink-0 rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]">✕</button>
        </div>

        {/* ── Setup required banner ── */}
        {!isConfigured && (
          <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-5">
            <div className="flex items-start gap-3 px-4 py-3.5 bg-[oklch(0.82_0.14_80/0.10)] border border-[oklch(0.82_0.14_80/0.3)] rounded-[10px]">
              <Icons.Activity style={{ width: 14, height: 14, color: 'var(--warn)', flexShrink: 0, marginTop: 1 }} />
              <div className="flex flex-col gap-0.5">
                <span className="text-[13px] font-semibold text-[var(--warn)]">Setup required</span>
                <span className="text-[12px] text-[var(--text-faint)]">Configure an embedding model and credential before adding documents.</span>
              </div>
            </div>

            {/* Embedding model */}
            <div className="flex flex-col gap-2">
              <label className="text-[12px] font-semibold text-[var(--text-mute)]">Embedding model</label>
              <div className="flex flex-col gap-3">
                {(['OpenAI', 'Google', 'Mistral'] as const).map(provider => (
                  <div key={provider}>
                    <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)] mb-1.5 block">{provider}</span>
                    <div className="flex flex-col gap-1.5">
                      {EMBEDDING_MODELS.filter(m => m.provider === provider).map(m => (
                        <label key={m.id} onClick={() => { setSetupModel(m.id); setSetupCredId('') }}
                          className={`flex items-center gap-3 px-3 py-2.5 rounded-[9px] border cursor-pointer transition-colors ${setupModel === m.id ? 'bg-[var(--surface)] border-[var(--border-soft)]' : 'bg-[var(--bg)] border-[var(--border-faint)] hover:border-[var(--border-soft)]'}`}>
                          <input type="radio" name="setup-model" value={m.id} checked={setupModel === m.id} readOnly className="accent-[var(--text)]" />
                          <div className="flex flex-col gap-0.5">
                            <span className="text-[13px] font-medium text-[var(--text)]">{m.label}</span>
                            <span className="text-[11px] font-mono text-[var(--text-faint)]">{m.dims.toLocaleString()} dimensions</span>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Credential */}
            <div className="flex flex-col gap-2">
              <label className="text-[12px] font-semibold text-[var(--text-mute)]">{selectedSetupModel?.provider} credential</label>
              {relevantCreds.length === 0 ? (
                <div className="flex items-center gap-2 px-3 py-2.5 bg-[oklch(0.82_0.14_80/0.10)] border border-[oklch(0.82_0.14_80/0.3)] rounded-[9px]">
                  <Icons.Activity style={{ width: 13, height: 13, color: 'var(--warn)' }} />
                  <span className="text-[12px] text-[var(--warn)]">No {selectedSetupModel?.provider} credentials. Add one in Connections first.</span>
                </div>
              ) : (
                <Dropdown className="w-full">
                  <DropdownTrigger className="w-full">
                    <div className="flex items-center justify-between h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] cursor-pointer hover:border-[var(--border-soft)] transition-colors">
                      <span className={selectedSetupCred ? 'text-[var(--text)]' : 'text-[var(--text-faint)]'}>
                        {selectedSetupCred?.name ?? `Select ${selectedSetupModel?.provider} credential…`}
                      </span>
                      <Icons.Caret style={{ width: 11, height: 11, color: 'var(--text-faint)' }} />
                    </div>
                  </DropdownTrigger>
                  <DropdownContent className="w-full">
                    {relevantCreds.map(c => (
                      <DropdownItem key={c.id} onClick={() => setSetupCredId(c.id)} className={setupCredId === c.id ? 'bg-[var(--surface)]' : ''}>
                        <div className="flex items-center justify-between w-full">
                          <span>{c.name}</span>
                          {setupCredId === c.id && <Icons.Check style={{ width: 13, height: 13, color: 'var(--ok)' }} />}
                        </div>
                      </DropdownItem>
                    ))}
                  </DropdownContent>
                </Dropdown>
              )}
            </div>

            {/* Chunking */}
            <div className="flex flex-col gap-3">
              <label className="text-[12px] font-semibold text-[var(--text-mute)]">Chunking</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Min size', unit: 'chars', val: setupMinChunk, set: setSetupMinChunk, min: 50 },
                  { label: 'Max size', unit: 'tokens', val: setupMaxTokens, set: setSetupMaxTokens, min: 128 },
                  { label: 'Overlap', unit: 'tokens', val: setupOverlap, set: setSetupOverlap, min: 0 },
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

              <div className="flex flex-col gap-1">
                <span className="text-[11px] text-[var(--text-faint)]">Strategy</span>
                <Dropdown className="w-full">
                  <DropdownTrigger className="w-full">
                    <div className="flex items-center justify-between h-[34px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[8px] text-[12.5px] text-[var(--text)] cursor-pointer hover:border-[var(--border-soft)] transition-colors">
                      <span>{selectedSetupStrategy?.label ?? 'Auto'}</span>
                      <Icons.Caret style={{ width: 10, height: 10, color: 'var(--text-faint)' }} />
                    </div>
                  </DropdownTrigger>
                  <DropdownContent className="w-full">
                    {CHUNKING_STRATEGIES.map(s => (
                      <DropdownItem key={s.id} onClick={() => setSetupStrategy(s.id)} className={setupStrategy === s.id ? 'bg-[var(--surface)]' : ''}>
                        <div className="flex flex-col gap-0.5">
                          <span className="text-[13px] font-medium">{s.label}</span>
                          <span className="text-[11px] text-[var(--text-faint)]">{s.desc}</span>
                        </div>
                      </DropdownItem>
                    ))}
                  </DropdownContent>
                </Dropdown>
              </div>
            </div>

            {setupError && <p className="text-[12px] text-[var(--err)]">{setupError}</p>}

            <button
              onClick={handleSaveSetup}
              disabled={setupSaving || !setupCredId}
              className="btn btn-primary self-end"
            >
              {setupSaving ? 'Saving…' : 'Save & continue'}
            </button>
          </div>
        )}

        {/* Tab nav — only shown when configured */}
        {isConfigured && <div className="flex items-center gap-1 px-5 py-3 border-b border-[var(--border-faint)] shrink-0">
          {([['docs', 'Documents'], ['add', 'Add document'], ['search', 'Test search']] as const).map(([id, label]) => (
            <button
              key={id}
              onClick={() => setPanel(id)}
              className={`px-3 py-1.5 rounded-[7px] text-[12.5px] font-medium transition-colors ${panel === id ? 'bg-[var(--surface)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]' : 'text-[var(--text-mute)] hover:text-[var(--text)]'}`}
            >
              {label}
              {id === 'docs' && detail && (
                <span className="ml-1.5 font-mono text-[10.5px] text-[var(--text-faint)]">{detail.documents.length}</span>
              )}
            </button>
          ))}
        </div>}

        {/* Body — only shown when configured */}
        {isConfigured && <div className="flex-1 overflow-y-auto p-5">

          {/* ── Documents tab ── */}
          {panel === 'docs' && (
            isLoading ? (
              <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
                <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
                Loading…
              </div>
            ) : detail?.documents.length === 0 ? (
              <div className="flex flex-col items-center gap-3 py-12 text-center">
                <Icons.Doc style={{ width: 20, height: 20, color: 'var(--text-dim)' }} />
                <div className="flex flex-col gap-1">
                  <span className="text-[13px] font-medium text-[var(--text-mute)]">No documents yet</span>
                  <span className="text-[12px] text-[var(--text-faint)]">Add a document to start indexing content.</span>
                </div>
                <button className="btn btn-primary mt-2" onClick={() => setPanel('add')}>
                  <Icons.Plus style={{ width: 13, height: 13 }} /> Add document
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {detail?.documents.map(doc => {
                  const isIndexed = doc.status === 'indexed'
                  const isFailed  = doc.status === 'failed'
                  const isPending = doc.status === 'pending'
                  const isReindexing = reindexDoc.isPending && (reindexDoc.variables as string | undefined) === doc.id

                  return (
                    <div key={doc.id} className="flex items-center gap-3 px-4 py-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px] hover:border-[var(--border-soft)] transition-colors group">

                      {/* Status indicator dot */}
                      <div
                        className={`w-[7px] h-[7px] rounded-full shrink-0 ${
                          isIndexed ? 'bg-[var(--ok)]' :
                          isFailed  ? 'bg-[var(--err)]' :
                          'bg-[var(--warn)]'
                        }`}
                        title={doc.status}
                      />

                      {/* Doc info */}
                      <div className="flex flex-col gap-0.5 flex-1 min-w-0">
                        <span className="text-[13px] font-medium text-[var(--text)] truncate">{doc.name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-mono text-[var(--text-faint)]">
                            {doc.chunk_count} chunk{doc.chunk_count !== 1 ? 's' : ''} · {doc.source_type} · {new Date(doc.created_at).toLocaleDateString()}
                          </span>
                          {/* Status badge */}
                          <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-[4px] ${
                            isIndexed ? 'bg-[oklch(0.78_0.14_145/0.12)] text-[var(--ok)]' :
                            isFailed  ? 'bg-[oklch(0.70_0.18_22/0.12)] text-[var(--err)]' :
                            'bg-[oklch(0.82_0.14_80/0.12)] text-[var(--warn)]'
                          }`}>
                            {isIndexed ? 'indexed' : isFailed ? 'failed' : 'pending'}
                          </span>
                        </div>
                      </div>

                      {/* Reindex button — shown for pending/failed docs that have raw_content */}
                      {(isPending || isFailed) && (
                        <button
                          onClick={() => {
                            reindexDoc.mutate(doc.id, {
                              onSuccess: () => toast('Document reindexed', { variant: 'ok' }),
                              onError: (err) => toast('Reindex failed', {
                                variant: 'err',
                                description: err instanceof Error ? err.message : 'Try again.',
                              }),
                            })
                          }}
                          disabled={isReindexing}
                          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-[7px] text-[11.5px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:border-[var(--border-soft)] hover:text-[var(--text)] transition-colors shrink-0 disabled:opacity-50"
                          title="Reindex this document"
                        >
                          {isReindexing ? (
                            <div className="w-3 h-3 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
                          ) : (
                            <Icons.Activity style={{ width: 11, height: 11 }} />
                          )}
                          {isReindexing ? 'Indexing…' : 'Reindex'}
                        </button>
                      )}

                      {/* Delete button */}
                      <button
                        onClick={() => handleDeleteDoc(doc.id, doc.name)}
                        className="w-[24px] h-[24px] rounded-[6px] flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)] transition-all shrink-0"
                        title="Delete document"
                      >
                        <Icons.Trash style={{ width: 12, height: 12 }} />
                      </button>
                    </div>
                  )
                })}
              </div>
            )
          )}

          {/* ── Add document tab ── */}
          {panel === 'add' && (
            <div className="flex flex-col gap-5">
              {/* Source type tabs */}
              <div className="flex items-center bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] p-[3px] gap-[2px] w-fit">
                {([['text', 'Paste text'], ['file', 'Upload file'], ['url', 'From URL']] as const).map(([t, label]) => (
                  <button
                    key={t}
                    onClick={() => setAddTab(t)}
                    className={`px-4 py-1.5 rounded-[6px] text-[12.5px] font-medium transition-colors ${addTab === t ? 'bg-[var(--surface)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]' : 'text-[var(--text-mute)] hover:text-[var(--text)]'}`}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {addTab === 'text' && (
                <div className="flex flex-col gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11.5px] font-medium text-[var(--text-mute)]">Document name</label>
                    <input
                      type="text"
                      value={textName}
                      onChange={e => setTextName(e.target.value)}
                      placeholder="e.g. Refund Policy"
                      className="h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11.5px] font-medium text-[var(--text-mute)]">Content</label>
                    <textarea
                      value={textBody}
                      onChange={e => setTextBody(e.target.value)}
                      placeholder="Paste your document text here…"
                      rows={10}
                      className="px-3 py-2.5 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors resize-none font-mono"
                    />
                    <span className="text-[11px] text-[var(--text-dim)] font-mono">{textBody.length.toLocaleString()} chars</span>
                  </div>
                  <button
                    onClick={handleAddText}
                    disabled={!textName.trim() || !textBody.trim() || isBusy}
                    className="btn btn-primary self-end"
                  >
                    {addText.isPending ? 'Indexing…' : 'Add & index'}
                  </button>
                </div>
              )}

              {addTab === 'file' && (
                <div className="flex flex-col gap-4">
                  <input ref={fileInputRef} type="file" accept=".txt,.pdf,.md,.csv" className="hidden" onChange={handleFileUpload} />
                  <div
                    className="flex flex-col items-center gap-3 py-12 border-2 border-dashed border-[var(--border-faint)] rounded-[12px] cursor-pointer hover:border-[var(--border-soft)] transition-colors"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Icons.Folder style={{ width: 24, height: 24, color: 'var(--text-dim)' }} />
                    <div className="text-center">
                      <p className="text-[13px] font-medium text-[var(--text-mute)]">Click to upload a file</p>
                      <p className="text-[12px] text-[var(--text-faint)] mt-1">PDF, TXT, MD, CSV supported</p>
                    </div>
                    {uploadDoc.isPending && (
                      <div className="flex items-center gap-2 text-[12px] text-[var(--text-faint)]">
                        <div className="w-3.5 h-3.5 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
                        Uploading and indexing…
                      </div>
                    )}
                  </div>
                </div>
              )}

              {addTab === 'url' && (
                <div className="flex flex-col gap-4">
                  <p className="text-[12.5px] text-[var(--text-faint)]">
                    Paste a URL — fuse will fetch the page, strip HTML, and index the text content.
                  </p>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[11.5px] font-medium text-[var(--text-mute)]">URL</label>
                    <input
                      type="url"
                      value={urlValue}
                      onChange={e => setUrlValue(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && handleAddUrl()}
                      placeholder="https://docs.example.com/refund-policy"
                      className="h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] font-mono text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors"
                    />
                  </div>
                  <button
                    onClick={handleAddUrl}
                    disabled={!urlValue.trim() || isBusy}
                    className="btn btn-primary self-end"
                  >
                    {addUrl.isPending ? 'Fetching & indexing…' : 'Fetch & index'}
                  </button>
                </div>
              )}

              {(addText.isError || uploadDoc.isError || addUrl.isError) && (
                <p className="text-[12px] text-[var(--err)]">
                  {(addText.error ?? uploadDoc.error ?? addUrl.error)?.message ?? 'Something went wrong'}
                </p>
              )}
            </div>
          )}

          {/* ── Search tab ── */}
          {panel === 'search' && (
            <div className="flex flex-col gap-5">
              <p className="text-[12.5px] text-[var(--text-faint)]">
                Test your knowledge base — type a natural language query and see which document chunks get retrieved.
              </p>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSearch()}
                  placeholder="What is your refund policy?"
                  className="flex-1 h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors"
                />
                <button
                  onClick={handleSearch}
                  disabled={!query.trim() || search.isPending}
                  className="btn btn-primary shrink-0"
                >
                  {search.isPending ? '…' : 'Search'}
                </button>
              </div>

              {results.length > 0 && (
                <div className="flex flex-col gap-3">
                  <span className="text-[11.5px] font-mono text-[var(--text-dim)] uppercase tracking-widest">
                    {results.length} result{results.length !== 1 ? 's' : ''}
                  </span>
                  {results.map((r, i) => (
                    <div key={r.id} className="flex flex-col gap-2 p-4 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px]">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-[11.5px] font-mono text-[var(--text-faint)]">chunk #{r.chunk_index} · match {i + 1}</span>
                        <span className={`text-[11px] font-mono font-semibold px-2 py-0.5 rounded-[4px] ${r.score > 0.8 ? 'bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]' : r.score > 0.6 ? 'bg-[oklch(0.82_0.14_80/0.16)] text-[var(--warn)]' : 'bg-[var(--surface)] text-[var(--text-mute)]'}`}>
                          {(r.score * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <p className="text-[12.5px] text-[var(--text-mute)] leading-relaxed line-clamp-4">{r.content}</p>
                    </div>
                  ))}
                </div>
              )}

              {search.isError && (
                <p className="text-[12px] text-[var(--err)]">{search.error?.message}</p>
              )}
            </div>
          )}
        </div>}

        {/* Footer CTA */}
        {isConfigured && panel === 'docs' && (
          <div className="px-5 py-4 border-t border-[var(--border-faint)] shrink-0">
            <button className="btn btn-primary w-full justify-center" onClick={() => setPanel('add')}>
              <Icons.Plus style={{ width: 13, height: 13 }} /> Add document
            </button>
          </div>
        )}
      </div>
    </>,
    document.body
  )
}

import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm } from '@/shared/components'
import {
  useKBDetail, useUploadDoc, useAddTextDoc, useAddUrlDoc, useDeleteDoc, useReindexDoc,
} from '../hooks/useKnowledge'
import { APP_ROUTES } from '@/shared/constants/routes'
import { ConnectorModal } from '../components/ConnectorModal'
import { KBSettingsPanel } from '../components/KBSettingsPanel'



export function KnowledgeDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const confirm = useConfirm()

  const { data: kb, isLoading, refetch } = useKBDetail(id ?? '')
  const uploadDoc  = useUploadDoc(id ?? '')
  const addTextDoc = useAddTextDoc(id ?? '')
  const addUrlDoc  = useAddUrlDoc(id ?? '')
  const deleteDoc  = useDeleteDoc(id ?? '')

  const [connectorOpen, setConnectorOpen] = useState(false)
  const [settingsOpen, setSettingsOpen]   = useState(false)
  const reindexDoc = useReindexDoc(id ?? '')
  const [addMode, setAddMode]             = useState<'file' | 'text' | 'url' | null>(null)
  const [textName, setTextName]           = useState('')
  const [textBody, setTextBody]           = useState('')
  const [urlValue, setUrlValue]           = useState('')
  const [isDragging, setIsDragging]       = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Pick up files queued from the creation modal
  useEffect(() => {
    if (!id) return
    const pendingFiles = (window as unknown as Record<string, unknown>)[`__kb_files_${id}`] as File[] | undefined
    if (pendingFiles && pendingFiles.length > 0) {
      delete (window as unknown as Record<string, unknown>)[`__kb_files_${id}`]
      sessionStorage.removeItem(`kb-pending-files-${id}`)
      ;(async () => {
        for (const file of pendingFiles) {
          try {
            await uploadDoc.mutateAsync(file)
          } catch { /* individual failures won't block others */ }
        }
        await refetch()
        toast(`${pendingFiles.length} file${pendingFiles.length > 1 ? 's' : ''} indexed`, { variant: 'ok' })
      })()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  const handleFileUpload = async (files: FileList | File[]) => {
    const arr = Array.from(files)
    let ok = 0
    let lastErr: Error | null = null
    for (const file of arr) {
      try { await uploadDoc.mutateAsync(file); ok++ }
      catch (e) { lastErr = e instanceof Error ? e : new Error(String(e)) }
    }
    if (ok) toast(`${ok} file${ok > 1 ? 's' : ''} indexed`, { variant: 'ok' })
    if (lastErr) toast('Upload failed', { variant: 'err', description: lastErr.message })
    setAddMode(null)
  }

  const handleAddText = async () => {
    if (!textName.trim() || !textBody.trim()) return
    await addTextDoc.mutateAsync({ name: textName, text: textBody })
    toast('Document indexed', { variant: 'ok', description: `"${textName}" added.` })
    setTextName(''); setTextBody(''); setAddMode(null)
  }

  const handleAddUrl = async () => {
    if (!urlValue.trim()) return
    await addUrlDoc.mutateAsync(urlValue.trim())
    toast('URL indexed', { variant: 'ok' })
    setUrlValue(''); setAddMode(null)
  }

  const handleDeleteDoc = async (docId: string, docName: string) => {
    const ok = await confirm({ title: 'Delete document', message: `Delete "${docName}"?`, confirmText: 'Delete', variant: 'danger' })
    if (!ok) return
    await deleteDoc.mutateAsync(docId)
    toast('Deleted', { variant: 'ok' })
  }

  const isBusy = uploadDoc.isPending || addTextDoc.isPending || addUrlDoc.isPending

  if (isLoading) return (
    <div className="view-body">
      <div className="flex items-center gap-3 py-12 text-[13px] text-[var(--text-faint)]">
        <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
        Loading…
      </div>
    </div>
  )

  if (!kb) return <div className="view-body"><p className="text-[13px] text-[var(--text-faint)]">Not found.</p></div>

  return (
    <div className="view-body">
      {/* Header */}
      <div className="page-head">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <button onClick={() => navigate(APP_ROUTES.KNOWLEDGE)}
              className="w-[22px] h-[22px] rounded-[6px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors shrink-0">
              <Icons.CaretRight style={{ width: 12, height: 12, transform: 'rotate(180deg)' }} />
            </button>
            <span className="eyebrow">Knowledge base</span>
          </div>
          <h1 className="truncate">{kb.name}</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={() => setSettingsOpen(true)}>
            <Icons.Settings style={{ width: 14, height: 14 }} />
            Configure
          </button>
          <button className="btn btn-secondary" onClick={() => setConnectorOpen(true)}>
            <Icons.Plug style={{ width: 14, height: 14 }} /> New connector
          </button>
          <button className="btn btn-primary" onClick={() => setAddMode('file')}>
            <Icons.Plus style={{ width: 14, height: 14 }} /> New document
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center flex-wrap bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px] overflow-hidden">
        {[
          { label: 'Documents', value: kb.document_count },
          { label: 'Chunks', value: kb.total_chunks.toLocaleString() },
          { label: 'Strategy', value: kb.chunking_strategy, mono: true },
          { label: 'Max chunk', value: `${kb.max_chunk_tokens} tokens`, mono: true },
        ].map((item, i, arr) => (
          <div key={item.label} className={`flex flex-col gap-1 py-3 px-4 flex-1 ${i < arr.length - 1 ? 'border-r border-[var(--border-faint)]' : ''}`}>
            <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)]">{item.label}</span>
            <span className={`text-[13.5px] font-medium text-[var(--text)] ${item.mono ? 'font-mono text-[12px]' : ''}`}>{item.value}</span>
          </div>
        ))}
      </div>



      {/* Add mode inline panel */}
      {addMode && (
        <div className="flex flex-col gap-4 p-5 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px]">
          {/* Tab bar */}
          <div className="flex items-center gap-1 bg-[var(--surface)] border border-[var(--border-faint)] rounded-[8px] p-[3px] w-fit">
            {(['file', 'text', 'url'] as const).map(m => (
              <button key={m} onClick={() => setAddMode(m)}
                className={`px-3 py-1 rounded-[5px] text-[12px] font-medium capitalize transition-colors ${addMode === m ? 'bg-[var(--bg-2)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]' : 'text-[var(--text-mute)] hover:text-[var(--text)]'}`}>
                {m === 'file' ? 'Upload file' : m === 'text' ? 'Paste text' : 'From URL'}
              </button>
            ))}
            <div className="ml-1 w-px h-4 bg-[var(--border-faint)]" />
            <button onClick={() => setAddMode(null)} className="px-2 py-1 text-[11px] text-[var(--text-dim)] hover:text-[var(--text-mute)] transition-colors">Cancel</button>
          </div>

          {addMode === 'file' && (
            <>
              <input ref={fileInputRef} type="file" multiple accept=".pdf,.doc,.docx,.txt,.csv,.xls,.xlsx,.md,.ppt,.pptx,.html,.jsonl" className="hidden"
                onChange={e => e.target.files && handleFileUpload(e.target.files)} />
              <div
                onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={e => { e.preventDefault(); setIsDragging(false); handleFileUpload(e.dataTransfer.files) }}
                onClick={() => fileInputRef.current?.click()}
                className={`flex flex-col items-center gap-2 py-10 border-2 border-dashed rounded-[10px] cursor-pointer transition-colors ${isDragging ? 'border-[var(--text)] bg-[var(--surface)]' : 'border-[var(--border-faint)] hover:border-[var(--border-soft)] hover:bg-[var(--surface)]'}`}>
                <Icons.Folder style={{ width: 24, height: 24, color: 'var(--text-dim)' }} />
                <div className="text-center">
                  <p className="text-[13px] font-medium text-[var(--text-mute)]">Drop files here or click to browse</p>
                  <p className="text-[11.5px] text-[var(--text-faint)] mt-1">PDF, DOC, DOCX, TXT, CSV, XLS, XLSX, MD, PPT, PPTX, HTML, JSONL</p>
                </div>
                {uploadDoc.isPending && (
                  <div className="flex items-center gap-2 text-[12px] text-[var(--text-faint)]">
                    <div className="w-3 h-3 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
                    Indexing…
                  </div>
                )}
              </div>
            </>
          )}

          {addMode === 'text' && (
            <div className="flex flex-col gap-3">
              <input type="text" value={textName} onChange={e => setTextName(e.target.value)} placeholder="Document name"
                className="h-[38px] px-3 bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors" />
              <textarea value={textBody} onChange={e => setTextBody(e.target.value)} placeholder="Paste document content here…" rows={8}
                className="px-3 py-2.5 bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] text-[13px] font-mono text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none resize-none focus:border-[var(--border)] transition-colors" />
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-[var(--text-dim)]">{textBody.length.toLocaleString()} chars</span>
                <button onClick={handleAddText} disabled={!textName.trim() || !textBody.trim() || isBusy} className="btn btn-primary">
                  {addTextDoc.isPending ? 'Indexing…' : 'Add & index'}
                </button>
              </div>
            </div>
          )}

          {addMode === 'url' && (
            <div className="flex flex-col gap-3">
              <p className="text-[12.5px] text-[var(--text-faint)]">fuse fetches the page, strips HTML, and indexes the text content.</p>
              <div className="flex gap-2">
                <input type="url" value={urlValue} onChange={e => setUrlValue(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleAddUrl()}
                  placeholder="https://docs.example.com/page"
                  className="flex-1 h-[38px] px-3 bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] text-[13px] font-mono text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors" />
                <button onClick={handleAddUrl} disabled={!urlValue.trim() || isBusy} className="btn btn-primary shrink-0">
                  {addUrlDoc.isPending ? 'Fetching…' : 'Fetch & index'}
                </button>
              </div>
            </div>
          )}

          {(addTextDoc.isError || uploadDoc.isError || addUrlDoc.isError) && (
            <p className="text-[12px] text-[var(--err)]">
              {((addTextDoc.error ?? uploadDoc.error ?? addUrlDoc.error) as Error)?.message}
            </p>
          )}
        </div>
      )}

      {/* Document list */}
      {kb.documents.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16">
          <Icons.Doc style={{ width: 24, height: 24, color: 'var(--text-dim)' }} />
          <div className="text-center">
            <p className="text-[13px] font-medium text-[var(--text-mute)]">No documents yet</p>
            <p className="text-[12px] text-[var(--text-faint)] mt-0.5">Upload a file, paste text, or connect a source.</p>
          </div>
          <button className="btn btn-primary" onClick={() => setAddMode('file')}>
            <Icons.Plus style={{ width: 13, height: 13 }} /> Add document
          </button>
        </div>
      ) : (
        <div className="panel">
          <div className="table">
            <div className="table-head" style={{ gridTemplateColumns: '10px minmax(0,1fr) 72px 72px 110px auto 28px' }}>
              <span></span><span>Name</span><span>Type</span><span>Chunks</span><span>Added</span><span>Status</span><span></span>
            </div>
            {kb.documents.map(doc => {
              const isIndexed    = doc.status === 'indexed'
              const isFailed     = doc.status === 'failed'
              const isPending    = doc.status === 'pending'
              const isReindexing = reindexDoc.isPending && (reindexDoc.variables as string | undefined) === doc.id

              return (
                <div
                  key={doc.id}
                  className="table-row group cursor-pointer"
                  style={{ gridTemplateColumns: '10px minmax(0,1fr) 72px 72px 110px auto 28px' }}
                  onClick={() => navigate(APP_ROUTES.KNOWLEDGE_DOCUMENT(id!, doc.id))}
                >
                  {/* Status dot */}
                  <div
                    className={`w-[7px] h-[7px] rounded-full self-center ${
                      isIndexed ? 'bg-[var(--ok)]' :
                      isFailed  ? 'bg-[var(--err)]' :
                      'bg-[var(--warn)]'
                    }`}
                    title={doc.status}
                  />

                  <span className="row-name">{doc.name}</span>
                  <span className="row-mono capitalize">{doc.source_type}</span>
                  <span className="row-mono">{doc.chunk_count}</span>
                  <span className="row-mono text-[var(--text-dim)]">
                    {new Date(doc.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>

                  {/* Status badge + reindex button */}
                  <span className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                    <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-[4px] whitespace-nowrap ${
                      isIndexed ? 'bg-[oklch(0.78_0.14_145/0.12)] text-[var(--ok)]' :
                      isFailed  ? 'bg-[oklch(0.70_0.18_22/0.12)] text-[var(--err)]' :
                      'bg-[oklch(0.82_0.14_80/0.12)] text-[var(--warn)]'
                    }`}>
                      {isIndexed ? 'indexed' : isFailed ? 'failed' : 'pending'}
                    </span>
                    {(isPending || isFailed) && (
                      <button
                        disabled={isReindexing}
                        onClick={() => {
                          reindexDoc.mutate(doc.id, {
                            onSuccess: () => toast('Document reindexed', { variant: 'ok' }),
                            onError: (err) => toast('Reindex failed', {
                              variant: 'err',
                              description: err instanceof Error ? err.message : 'Try again.',
                            }),
                          })
                        }}
                        className="flex items-center gap-1 px-2 py-0.5 rounded-[6px] text-[11px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:border-[var(--border-soft)] hover:text-[var(--text)] transition-colors shrink-0 disabled:opacity-50"
                        title="Reindex this document"
                      >
                        {isReindexing
                          ? <div className="w-2.5 h-2.5 border-[1.5px] border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
                          : <Icons.Activity style={{ width: 10, height: 10 }} />
                        }
                        {isReindexing ? 'Indexing…' : 'Reindex'}
                      </button>
                    )}
                  </span>

                  {/* Delete */}
                  <span className="flex items-center justify-end" onClick={e => e.stopPropagation()}>
                    <button
                      onClick={() => handleDeleteDoc(doc.id, doc.name)}
                      className="w-[22px] h-[22px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)] transition-all"
                    >
                      <Icons.Trash style={{ width: 12, height: 12 }} />
                    </button>
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Connector modal */}
      {connectorOpen && (
        <ConnectorModal kbId={id!} onClose={() => setConnectorOpen(false)} onConnected={() => { setConnectorOpen(false); refetch() }} />
      )}

      {/* Settings panel */}
      {settingsOpen && kb && (
        <KBSettingsPanel
          kb={kb}
          onClose={() => setSettingsOpen(false)}
          onSaved={() => { refetch(); setSettingsOpen(false) }}
        />
      )}
    </div>
  )
}

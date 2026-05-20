import React, { useState } from 'react'
import { Plus, Database, Trash2, Upload, FileText, Search, ChevronRight, X, Loader2 } from 'lucide-react'
import { useKnowledgeBases, useKBDocuments, useKBSearch } from './hooks'
import { Button } from '@/components/ui'
import apiClient from '@/lib/api/client'

// ── Types ──────────────────────────────────────────────────────────────────────

interface KnowledgeBase {
  id: string
  name: string
  description: string | null
  embedding_model: string
  embedding_credential_id: string | null
  document_count: number
  created_at: string
}

// ── Create KB Modal ────────────────────────────────────────────────────────────

const CreateKBModal: React.FC<{ onClose: () => void; onCreated: () => void }> = ({ onClose, onCreated }) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [credentialId, setCredentialId] = useState('')
  const [model, setModel] = useState('text-embedding-3-small')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!name.trim()) return
    setLoading(true)
    setError(null)
    try {
      await apiClient.post('/kb/', {
        name: name.trim(),
        description: description.trim() || null,
        embedding_model: model,
        embedding_credential_id: credentialId.trim() || null,
      })
      onCreated()
      onClose()
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to create knowledge base')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-6 w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold text-[15px]">New Knowledge Base</h2>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-white transition-colors"><X className="w-4 h-4" /></button>
        </div>

        <div className="flex flex-col gap-4">
          <div>
            <label className="text-[12px] text-[var(--text-muted)] font-medium mb-1 block">Name *</label>
            <input
              autoFocus
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Product Documentation"
              className="w-full bg-[var(--bg-surface-2)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-[13px] text-white focus:outline-none focus:border-[var(--border-focus)]"
            />
          </div>
          <div>
            <label className="text-[12px] text-[var(--text-muted)] font-medium mb-1 block">Description</label>
            <input
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Optional description"
              className="w-full bg-[var(--bg-surface-2)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-[13px] text-white focus:outline-none focus:border-[var(--border-focus)]"
            />
          </div>
          <div>
            <label className="text-[12px] text-[var(--text-muted)] font-medium mb-1 block">OpenAI Credential ID *</label>
            <input
              value={credentialId}
              onChange={e => setCredentialId(e.target.value)}
              placeholder="Paste your OpenAI credential ID"
              className="w-full bg-[var(--bg-surface-2)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-[13px] text-white focus:outline-none focus:border-[var(--border-focus)]"
            />
            <p className="text-[11px] text-[var(--text-muted)] mt-1">Find it in Settings → API Keys</p>
          </div>
          <div>
            <label className="text-[12px] text-[var(--text-muted)] font-medium mb-1 block">Embedding Model</label>
            <select
              value={model}
              onChange={e => setModel(e.target.value)}
              className="w-full bg-[var(--bg-surface-2)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-[13px] text-white focus:outline-none"
            >
              <option value="text-embedding-3-small">text-embedding-3-small (default)</option>
              <option value="text-embedding-3-large">text-embedding-3-large (higher quality)</option>
              <option value="text-embedding-ada-002">text-embedding-ada-002 (legacy)</option>
            </select>
          </div>

          {error && <p className="text-[12px] text-red-400">{error}</p>}

          <div className="flex gap-2 justify-end mt-2">
            <Button variant="ghost" size="sm" onClick={onClose}>Cancel</Button>
            <Button size="sm" onClick={submit} disabled={loading || !name.trim()}>
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Create'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── KB Detail Panel ────────────────────────────────────────────────────────────

const KBDetail: React.FC<{ kb: KnowledgeBase; onBack: () => void; onDelete: () => void }> = ({ kb, onBack, onDelete }) => {
  const { documents, loading: docsLoading, refetch } = useKBDocuments(kb.id)
  const [addText, setAddText] = useState(false)
  const [textName, setTextName] = useState('')
  const [textContent, setTextContent] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const { results, search, searching } = useKBSearch(kb.id)

  const submitText = async () => {
    if (!textName.trim() || !textContent.trim()) return
    setUploading(true)
    setUploadError(null)
    try {
      await apiClient.post(`/kb/${kb.id}/documents/text`, { name: textName.trim(), text: textContent.trim() })
      setAddText(false); setTextName(''); setTextContent('')
      refetch()
    } catch (e: any) {
      setUploadError(e?.response?.data?.detail || 'Failed to add document')
    } finally {
      setUploading(false)
    }
  }

  const uploadFile = async (file: File) => {
    setUploading(true); setUploadError(null)
    const form = new FormData()
    form.append('file', file)
    try {
      await apiClient.post(`/kb/${kb.id}/documents/upload`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      refetch()
    } catch (e: any) {
      setUploadError(e?.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const deleteDoc = async (docId: string) => {
    await apiClient.delete(`/kb/${kb.id}/documents/${docId}`)
    refetch()
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 mb-6">
        <button onClick={onBack} className="text-[var(--text-muted)] hover:text-white transition-colors text-[13px]">Knowledge Bases</button>
        <ChevronRight className="w-3.5 h-3.5 text-[var(--text-muted)]" />
        <span className="text-white text-[13px] font-medium">{kb.name}</span>
      </div>

      <div className="grid grid-cols-2 gap-6 flex-1 overflow-hidden">
        {/* Documents panel */}
        <div className="flex flex-col overflow-hidden">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[13px] font-semibold text-white">Documents ({documents.length})</h3>
            <div className="flex gap-2">
              <label className="cursor-pointer flex items-center gap-1.5 text-[12px] text-[var(--text-muted)] hover:text-white transition-colors px-2 py-1 rounded hover:bg-[var(--bg-surface-2)]">
                <Upload className="w-3.5 h-3.5" />
                Upload
                <input type="file" accept=".txt,.md,.pdf" className="hidden" onChange={e => e.target.files?.[0] && uploadFile(e.target.files[0])} />
              </label>
              <button onClick={() => setAddText(true)} className="flex items-center gap-1.5 text-[12px] text-[var(--text-muted)] hover:text-white transition-colors px-2 py-1 rounded hover:bg-[var(--bg-surface-2)]">
                <Plus className="w-3.5 h-3.5" /> Text
              </button>
            </div>
          </div>

          {uploadError && <p className="text-[12px] text-red-400 mb-2">{uploadError}</p>}
          {uploading && <div className="flex items-center gap-2 text-[12px] text-[var(--text-muted)] mb-2"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Processing...</div>}

          {addText && (
            <div className="border border-[var(--border-default)] rounded-lg p-3 mb-3 flex flex-col gap-2 bg-[var(--bg-surface-2)]">
              <input value={textName} onChange={e => setTextName(e.target.value)} placeholder="Document name" className="bg-[var(--bg-surface-3)] border border-[var(--border-default)] rounded px-2 py-1.5 text-[12px] text-white focus:outline-none w-full" />
              <textarea value={textContent} onChange={e => setTextContent(e.target.value)} placeholder="Paste text content..." rows={5} className="bg-[var(--bg-surface-3)] border border-[var(--border-default)] rounded px-2 py-1.5 text-[12px] text-white focus:outline-none w-full resize-none" />
              <div className="flex gap-2 justify-end">
                <button onClick={() => setAddText(false)} className="text-[12px] text-[var(--text-muted)] hover:text-white">Cancel</button>
                <button onClick={submitText} disabled={uploading} className="text-[12px] text-white bg-indigo-600 hover:bg-indigo-500 px-3 py-1 rounded transition-colors disabled:opacity-50">Add</button>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto flex flex-col gap-2">
            {docsLoading ? (
              <div className="flex items-center gap-2 text-[12px] text-[var(--text-muted)]"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading...</div>
            ) : documents.length === 0 ? (
              <p className="text-[12px] text-[var(--text-muted)] italic">No documents yet. Upload a file or add text.</p>
            ) : documents.map(doc => (
              <div key={doc.id} className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface-2)] group">
                <FileText className="w-4 h-4 text-[var(--text-muted)] flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] text-white truncate">{doc.name}</p>
                  <p className="text-[11px] text-[var(--text-muted)]">{doc.chunk_count} chunks · {doc.source_type}</p>
                </div>
                <button onClick={() => deleteDoc(doc.id)} className="opacity-0 group-hover:opacity-100 transition-opacity text-[var(--text-muted)] hover:text-red-400">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Search panel */}
        <div className="flex flex-col overflow-hidden">
          <h3 className="text-[13px] font-semibold text-white mb-3">Test Search</h3>
          <div className="flex gap-2 mb-3">
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && search(query)}
              placeholder="Search your knowledge base..."
              className="flex-1 bg-[var(--bg-surface-2)] border border-[var(--border-default)] rounded-lg px-3 py-2 text-[13px] text-white focus:outline-none focus:border-[var(--border-focus)]"
            />
            <button onClick={() => search(query)} disabled={searching || !query.trim()} className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg transition-colors disabled:opacity-50">
              {searching ? <Loader2 className="w-4 h-4 animate-spin text-white" /> : <Search className="w-4 h-4 text-white" />}
            </button>
          </div>
          <div className="flex-1 overflow-y-auto flex flex-col gap-2">
            {results.map((r, i) => (
              <div key={r.id} className="p-3 rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface-2)]">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] text-[var(--text-muted)]">Chunk #{i + 1}</span>
                  <span className="text-[11px] text-indigo-400 font-mono">{(r.score * 100).toFixed(1)}%</span>
                </div>
                <p className="text-[12px] text-white leading-relaxed line-clamp-6">{r.content}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export const KnowledgePage: React.FC = () => {
  const { kbs, loading, refetch } = useKnowledgeBases()
  const [showCreate, setShowCreate] = useState(false)
  const [selected, setSelected] = useState<KnowledgeBase | null>(null)

  const deleteKB = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this knowledge base and all its documents?')) return
    await apiClient.delete(`/kb/${id}`)
    refetch()
  }

  if (selected) {
    return (
      <div className="h-full p-8 overflow-hidden flex flex-col">
        <KBDetail kb={selected} onBack={() => setSelected(null)} onDelete={() => { setSelected(null); refetch() }} />
      </div>
    )
  }

  return (
    <div className="h-full p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-[20px] font-bold text-white">Knowledge Bases</h1>
            <p className="text-[13px] text-[var(--text-muted)] mt-1">Upload documents and enable semantic search in your workflows</p>
          </div>
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus className="w-3.5 h-3.5 mr-1.5" /> New Knowledge Base
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center gap-2 text-[var(--text-muted)]"><Loader2 className="w-4 h-4 animate-spin" /> Loading...</div>
        ) : kbs.length === 0 ? (
          <div className="text-center py-24">
            <Database className="w-10 h-10 text-[var(--text-muted)] mx-auto mb-3" />
            <p className="text-[14px] text-[var(--text-muted)]">No knowledge bases yet</p>
            <p className="text-[12px] text-[var(--text-muted)] mt-1">Create one to start uploading documents</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {kbs.map(kb => (
              <div
                key={kb.id}
                onClick={() => setSelected(kb)}
                className="group p-4 rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-[var(--border-focus)] cursor-pointer transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-indigo-600/20 flex items-center justify-center flex-shrink-0">
                      <Database className="w-4 h-4 text-indigo-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13px] font-semibold text-white truncate">{kb.name}</p>
                      <p className="text-[11px] text-[var(--text-muted)]">{kb.document_count} documents</p>
                    </div>
                  </div>
                  <button onClick={e => deleteKB(kb.id, e)} className="opacity-0 group-hover:opacity-100 transition-opacity text-[var(--text-muted)] hover:text-red-400 ml-2">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                {kb.description && <p className="text-[12px] text-[var(--text-muted)] mt-2 line-clamp-2">{kb.description}</p>}
                <p className="text-[11px] text-[var(--text-muted)] mt-3 font-mono">{kb.embedding_model}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreate && <CreateKBModal onClose={() => setShowCreate(false)} onCreated={refetch} />}
    </div>
  )
}

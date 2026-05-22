import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm } from '@/shared/components'
import {
  useChunks, useCreateChunk, useUpdateChunk, useDeleteChunk,
} from '../hooks/useKnowledge'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { KBChunk } from '../types/knowledgeTypes'

export function KnowledgeDocumentView() {
  const { id: kbId, docId } = useParams<{ id: string; docId: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const confirm = useConfirm()

  const { data: chunks = [], isLoading } = useChunks(kbId ?? '', docId ?? '')
  const createChunk = useCreateChunk(kbId ?? '', docId ?? '')
  const updateChunk = useUpdateChunk(kbId ?? '')
  const deleteChunk = useDeleteChunk(kbId ?? '', docId ?? '')

  // Chunk editor state
  const [editingId, setEditingId]     = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [activeIdx, setActiveIdx]     = useState<number | null>(null)

  // New chunk form
  const [newContent, setNewContent]   = useState('')
  const [showNew, setShowNew]         = useState(false)

  const openEditor = (chunk: KBChunk) => {
    setEditingId(chunk.id)
    setEditContent(chunk.content)
    setActiveIdx(chunk.chunk_index)
  }

  const closeEditor = () => {
    setEditingId(null); setEditContent(''); setActiveIdx(null)
  }

  const handleSave = async () => {
    if (!editingId) return
    await updateChunk.mutateAsync({ chunkId: editingId, content: editContent })
    toast('Chunk updated', { variant: 'ok', description: 'Re-embedded with new content.' })
    closeEditor()
  }

  const handleDelete = async (chunk: KBChunk) => {
    const ok = await confirm({ title: 'Delete chunk', message: `Delete chunk #${chunk.chunk_index}? This cannot be undone.`, confirmText: 'Delete', variant: 'danger' })
    if (!ok) return
    await deleteChunk.mutateAsync(chunk.id)
    if (editingId === chunk.id) closeEditor()
    toast('Chunk deleted', { variant: 'ok' })
  }

  const handleCreateChunk = async () => {
    if (!newContent.trim()) return
    await createChunk.mutateAsync(newContent.trim())
    toast('Chunk added', { variant: 'ok', description: 'New chunk indexed.' })
    setNewContent(''); setShowNew(false)
  }

  const navigateChunk = (dir: 'prev' | 'next') => {
    if (activeIdx === null) return
    const target = dir === 'prev' ? activeIdx - 1 : activeIdx + 1
    const chunk = chunks.find(c => c.chunk_index === target)
    if (chunk) openEditor(chunk)
  }

  const editingChunk = chunks.find(c => c.id === editingId)

  if (isLoading) return (
    <div className="view-body">
      <div className="flex items-center gap-3 py-12 text-[13px] text-[var(--text-faint)]">
        <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
        Loading chunks…
      </div>
    </div>
  )

  return (
    <div className="view-body">
      {/* Header */}
      <div className="page-head">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <button onClick={() => navigate(APP_ROUTES.KNOWLEDGE_DETAIL(kbId!))}
              className="w-[22px] h-[22px] rounded-[6px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors shrink-0">
              <Icons.CaretRight style={{ width: 12, height: 12, transform: 'rotate(180deg)' }} />
            </button>
            <span className="eyebrow">{chunks.length} chunks</span>
          </div>
          <h1>Document</h1>
        </div>
        <button className="btn btn-primary" onClick={() => setShowNew(v => !v)}>
          <Icons.Plus style={{ width: 13, height: 13 }} /> New chunk
        </button>
      </div>

      {/* New chunk form */}
      {showNew && (
        <div className="flex flex-col gap-3 p-5 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px]">
          <label className="text-[12px] font-semibold text-[var(--text-mute)]">New chunk content</label>
          <textarea
            autoFocus
            value={newContent}
            onChange={e => setNewContent(e.target.value)}
            placeholder="Type or paste the chunk text…"
            rows={5}
            className="px-3 py-2.5 bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] text-[13px] font-mono text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none resize-none focus:border-[var(--border)] transition-colors"
          />
          <p className="text-[11px] font-mono text-[var(--text-dim)]">{newContent.length} chars</p>
          <div className="flex items-center justify-end gap-3">
            <button onClick={() => { setShowNew(false); setNewContent('') }} className="px-4 py-2 rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors">
              Cancel
            </button>
            <button onClick={handleCreateChunk} disabled={!newContent.trim() || createChunk.isPending} className="btn btn-primary">
              {createChunk.isPending ? 'Indexing…' : 'Add chunk'}
            </button>
          </div>
        </div>
      )}

      {/* Main layout: chunk list + editor side by side */}
      <div className={`flex gap-5 ${editingId ? 'items-start' : ''}`}>

        {/* Chunk list */}
        <div className={`flex flex-col gap-2 ${editingId ? 'w-[320px] shrink-0' : 'w-full'}`}>
          {chunks.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-12">
              <Icons.Doc style={{ width: 20, height: 20, color: 'var(--text-dim)' }} />
              <p className="text-[13px] text-[var(--text-faint)]">No chunks yet.</p>
            </div>
          ) : chunks.map(chunk => (
            <div
              key={chunk.id}
              onClick={() => openEditor(chunk)}
              className={`flex flex-col gap-2 p-4 rounded-[10px] border cursor-pointer transition-colors group ${editingId === chunk.id ? 'bg-[var(--surface)] border-[var(--border-soft)]' : 'bg-[var(--bg)] border-[var(--border-faint)] hover:border-[var(--border-soft)]'}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-[var(--text-dim)]">chunk #{chunk.chunk_index}</span>
                <div className="flex items-center gap-1">
                  {chunk.has_embedding && (
                    <span className="text-[9.5px] font-mono tracking-widest uppercase px-[6px] py-[2px] rounded-[3px] bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]">indexed</span>
                  )}
                  <button
                    onClick={e => { e.stopPropagation(); handleDelete(chunk) }}
                    className="w-[20px] h-[20px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-dim)] opacity-0 group-hover:opacity-100 hover:bg-[oklch(0.70_0.18_22/0.14)] hover:text-[var(--err)] transition-all"
                  >
                    <Icons.Trash style={{ width: 11, height: 11 }} />
                  </button>
                </div>
              </div>
              <p className={`text-[12.5px] text-[var(--text-mute)] leading-relaxed ${editingId ? 'line-clamp-3' : 'line-clamp-4'}`}>
                {chunk.content}
              </p>
              <span className="text-[10.5px] font-mono text-[var(--text-dim)]">{chunk.content.length} chars</span>
            </div>
          ))}
        </div>

        {/* Chunk editor */}
        {editingId && editingChunk && (
          <div className="flex-1 flex flex-col gap-4 p-5 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] sticky top-4">
            {/* Editor header */}
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-semibold text-[var(--text-mute)]">chunk #{editingChunk.chunk_index}</span>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => navigateChunk('prev')}
                  disabled={editingChunk.chunk_index === 0}
                  className="w-[26px] h-[26px] rounded-[6px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  title="Previous chunk"
                >
                  <Icons.CaretRight style={{ width: 12, height: 12, transform: 'rotate(180deg)' }} />
                </button>
                <button
                  onClick={() => navigateChunk('next')}
                  disabled={editingChunk.chunk_index >= chunks.length - 1}
                  className="w-[26px] h-[26px] rounded-[6px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  title="Next chunk"
                >
                  <Icons.CaretRight style={{ width: 12, height: 12 }} />
                </button>
                <button onClick={closeEditor} className="w-[26px] h-[26px] rounded-[6px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[12px] ml-1">
                  ✕
                </button>
              </div>
            </div>

            {/* Text editor */}
            <textarea
              value={editContent}
              onChange={e => setEditContent(e.target.value)}
              rows={14}
              className="px-3 py-2.5 bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[9px] text-[13px] font-mono text-[var(--text)] outline-none resize-none focus:border-[var(--border)] transition-colors leading-relaxed"
            />

            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono text-[var(--text-dim)]">{editContent.length} chars · {chunks.length} total chunks</span>
              <div className="flex items-center gap-2">
                <button onClick={closeEditor} className="px-3 py-1.5 rounded-[7px] text-[12.5px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors">
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={updateChunk.isPending || editContent === editingChunk.content}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[7px] bg-[var(--text)] text-[var(--bg)] text-[12.5px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors disabled:opacity-40 disabled:cursor-default"
                >
                  {updateChunk.isPending ? 'Saving…' : 'Save & re-index'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

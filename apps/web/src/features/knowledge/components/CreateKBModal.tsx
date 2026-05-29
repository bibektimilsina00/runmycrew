import { useState, useRef } from 'react'
import { createPortal } from 'react-dom'
import { Icons } from '@/shared/components/icons'
import {
  Dropdown, DropdownTrigger, DropdownContent, DropdownItem,
} from '@/shared/components/Dropdown'
import { useCreateKB } from '../hooks/useKnowledge'
import { CHUNKING_STRATEGIES } from '../types/knowledgeTypes'

interface Props {
  onClose: () => void
  onCreated: (kbId: string) => void
}

const ACCEPTED = '.pdf,.doc,.docx,.txt,.csv,.xls,.xlsx,.md,.ppt,.pptx,.html,.jsonl'
const ACCEPT_LABEL = 'PDF, DOC, DOCX, TXT, CSV, XLS, XLSX, MD, PPT, PPTX, HTML, JSONL (max 100MB each)'

export function CreateKBModal({ onClose, onCreated }: Props) {
  const createKB = useCreateKB()

  const [name, setName]           = useState('')
  const [description, setDescription] = useState('')
  const [minChunk, setMinChunk]   = useState(100)
  const [maxTokens, setMaxTokens] = useState(1024)
  const [overlap, setOverlap]     = useState(200)
  const [strategy, setStrategy]   = useState('auto')
  const [files, setFiles]         = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError]         = useState<string | null>(null)
  const fileInputRef              = useRef<HTMLInputElement>(null)

  const selectedStrategy = CHUNKING_STRATEGIES.find(s => s.id === strategy)

  const addFiles = (incoming: FileList | File[]) => {
    const arr = Array.from(incoming)
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name + f.size))
      return [...prev, ...arr.filter(f => !existing.has(f.name + f.size))]
    })
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false)
    addFiles(e.dataTransfer.files)
  }

  const handleCreate = async () => {
    if (!name.trim()) { setError('Name is required.'); return }
    setError(null)
    try {
      const kb = await createKB.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
        embedding_model: 'text-embedding-3-small',
        min_chunk_size: minChunk,
        max_chunk_tokens: maxTokens,
        overlap_tokens: overlap,
        chunking_strategy: strategy,
      })
      onCreated(kb.id)
      // Files are uploaded after creation in the detail page
      // Pass them via sessionStorage so the detail page can pick them up
      if (files.length > 0) {
        sessionStorage.setItem(`kb-pending-files-${kb.id}`, JSON.stringify(files.map(f => f.name)))
        // Store actual files in a global map since sessionStorage can't hold File objects
        ;(window as unknown as Record<string, unknown>)[`__kb_files_${kb.id}`] = files
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create.')
    }
  }

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[560px] max-h-[92vh] overflow-y-auto bg-[var(--bg-2)] border border-[var(--border)] rounded-[16px] flex flex-col shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]">

        {/* Header */}
        <div className="flex items-start justify-between px-6 pt-6 pb-4 shrink-0">
          <div>
            <h3 className="text-[16px] font-semibold text-[var(--text)] tracking-tight">Create Knowledge Base</h3>
            <p className="text-[12.5px] text-[var(--text-faint)] mt-1">Set up a new knowledge base with documents and chunking options</p>
          </div>
          <button onClick={onClose} className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px] shrink-0">✕</button>
        </div>

        <div className="px-6 pb-6 flex flex-col gap-5">
          {/* Name */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-semibold text-[var(--text-mute)]">Name</label>
            <input autoFocus type="text" value={name} onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreate()}
              placeholder="Enter knowledge base name"
              className="h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors" />
          </div>

          {/* Description */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-semibold text-[var(--text-mute)]">Description</label>
            <input type="text" value={description} onChange={e => setDescription(e.target.value)}
              placeholder="Describe this knowledge base (optional)"
              className="h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors" />
          </div>

          {/* Chunk settings */}
          <div className="flex flex-col gap-2">
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Min Chunk Size (characters)', val: minChunk, set: setMinChunk, min: 50, unit: '' },
                { label: 'Max Chunk Size (tokens)', val: maxTokens, set: setMaxTokens, min: 128, unit: '' },
                { label: 'Overlap (tokens)', val: overlap, set: setOverlap, min: 0, unit: '' },
              ].map(f => (
                <div key={f.label} className="flex flex-col gap-1.5">
                  <label className="text-[11.5px] font-medium text-[var(--text-mute)] leading-tight">{f.label}</label>
                  <input type="number" value={f.val} min={f.min}
                    onChange={e => f.set(Math.max(f.min, Number(e.target.value)))}
                    className="h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] outline-none focus:border-[var(--border)] transition-colors" />
                </div>
              ))}
            </div>
            <p className="text-[11px] font-mono text-[var(--text-dim)]">
              1 token ≈ 4 characters. Max chunk size and overlap are in tokens.
            </p>
          </div>

          {/* Chunking strategy */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-semibold text-[var(--text-mute)]">Chunking Strategy</label>
            <Dropdown className="w-full">
              <DropdownTrigger className="w-full">
                <div className="flex items-center justify-between h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] cursor-pointer hover:border-[var(--border-soft)] transition-colors">
                  <span>{selectedStrategy?.label ?? 'Auto'}</span>
                  <Icons.Caret style={{ width: 11, height: 11, color: 'var(--text-faint)' }} />
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
            {selectedStrategy && <p className="text-[11.5px] text-[var(--text-faint)]">{selectedStrategy.desc}</p>}
          </div>

          {/* Upload documents */}
          <div className="flex flex-col gap-2">
            <label className="text-[12px] font-semibold text-[var(--text-mute)]">Upload Documents</label>
            <input ref={fileInputRef} type="file" multiple accept={ACCEPTED} className="hidden"
              onChange={e => e.target.files && addFiles(e.target.files)} />

            <div
              onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`flex flex-col items-center gap-2 py-8 border-2 border-dashed rounded-[10px] cursor-pointer transition-colors ${isDragging ? 'border-[var(--text)] bg-[var(--surface)]' : 'border-[var(--border-faint)] hover:border-[var(--border-soft)] hover:bg-[var(--surface)]'}`}
            >
              <Icons.Folder style={{ width: 22, height: 22, color: 'var(--text-dim)' }} />
              <div className="text-center">
                <p className="text-[13px] font-medium text-[var(--text-mute)]">Drop files here or click to browse</p>
                <p className="text-[11px] text-[var(--text-faint)] mt-1 max-w-[380px]">{ACCEPT_LABEL}</p>
              </div>
            </div>

            {/* Queued files */}
            {files.length > 0 && (
              <div className="flex flex-col gap-1.5 mt-1">
                {files.map((f, i) => (
                  <div key={i} className="flex items-center gap-3 px-3 py-2 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[8px]">
                    <Icons.Doc style={{ width: 13, height: 13, color: 'var(--text-faint)', flexShrink: 0 }} />
                    <span className="flex-1 text-[12.5px] text-[var(--text-mute)] truncate">{f.name}</span>
                    <span className="text-[11px] font-mono text-[var(--text-dim)]">{(f.size / 1024 / 1024).toFixed(1)} MB</span>
                    <button onClick={e => { e.stopPropagation(); setFiles(prev => prev.filter((_, j) => j !== i)) }}
                      className="text-[var(--text-dim)] hover:text-[var(--err)] transition-colors text-[12px]">✕</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {error && <p className="text-[12px] text-[var(--err)]">{error}</p>}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-1 border-t border-[var(--border-faint)]">
            <button onClick={onClose} className="px-4 py-2 rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors">
              Cancel
            </button>
            <button onClick={handleCreate} disabled={createKB.isPending || !name.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors disabled:opacity-40 disabled:cursor-default">
              <Icons.Plus style={{ width: 13, height: 13 }} />
              {createKB.isPending ? 'Creating…' : files.length > 0 ? `Create & upload ${files.length} file${files.length > 1 ? 's' : ''}` : 'Create knowledge base'}
            </button>
          </div>
        </div>
      </div>
    </>,
    document.body
  )
}

import { useState } from 'react'
import { createPortal } from 'react-dom'
import { Icons } from '@/shared/components/icons'
import { useToast } from '@/shared/components'
import { useAddUrlDoc } from '../hooks/useKnowledge'

interface Props {
  kbId: string
  onClose: () => void
  onConnected: () => void
}

const SOURCES = [
  { id: 'notion',    name: 'Notion',     icon: '📝', desc: 'Sync pages and databases', available: true },
  { id: 'slack',     name: 'Slack',      icon: '💬', desc: 'Index channel messages', available: true },
  { id: 'github',    name: 'GitHub',     icon: '🐱', desc: 'Sync repo files and docs', available: true },
  { id: 'airtable',  name: 'Airtable',   icon: '📊', desc: 'Sync table records', available: false },
  { id: 'asana',     name: 'Asana',      icon: '🎯', desc: 'Sync tasks and projects', available: false },
  { id: 'discord',   name: 'Discord',    icon: '🎮', desc: 'Index server channels', available: false },
  { id: 'linear',    name: 'Linear',     icon: '📐', desc: 'Sync issues and docs', available: false },
  { id: 'jira',      name: 'Jira',       icon: '🔵', desc: 'Sync tickets and wikis', available: false },
  { id: 'confluence',name: 'Confluence', icon: '📚', desc: 'Sync spaces and pages', available: false },
  { id: 'gdrive',    name: 'Google Drive',icon: '📁', desc: 'Sync folders and docs', available: false },
  { id: 'dropbox',   name: 'Dropbox',    icon: '📦', desc: 'Sync files and folders', available: false },
  { id: 'website',   name: 'Website',    icon: '🌐', desc: 'Crawl and index URLs',  available: true },
]

export function ConnectorModal({ kbId, onClose, onConnected }: Props) {
  const { toast } = useToast()
  const addUrl = useAddUrlDoc(kbId)

  const [selected, setSelected]   = useState<string | null>(null)
  const [urlInput, setUrlInput]   = useState('')
  const [connecting, setConnecting] = useState(false)

  const handleConnect = async () => {
    if (selected === 'website' && !urlInput.trim()) return
    setConnecting(true)
    try {
      if (selected === 'website') {
        await addUrl.mutateAsync(urlInput.trim())
        toast('URL indexed', { variant: 'ok', description: 'Page content added to KB.' })
      } else {
        // Coming soon — just show toast
        toast('Coming soon', { variant: 'ok', description: `${SOURCES.find(s => s.id === selected)?.name} connector is in development.` })
      }
      onConnected()
    } catch (err) {
      toast('Failed', { variant: 'err', description: err instanceof Error ? err.message : 'Try again.' })
    } finally {
      setConnecting(false)
    }
  }

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[540px] max-h-[80vh] bg-[var(--bg-2)] border border-[var(--border)] rounded-[10px] flex flex-col shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]">

        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-faint)] shrink-0">
          <div>
            <h3 className="text-[15px] font-semibold text-[var(--text)] tracking-tight">Connect source</h3>
            <p className="text-[12px] text-[var(--text-faint)] mt-0.5">Sync an external source into this knowledge base</p>
          </div>
          <button onClick={onClose} className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          <div className="grid grid-cols-3 gap-2">
            {SOURCES.map(s => (
              <button
                key={s.id}
                onClick={() => setSelected(s.id)}
                className={`flex flex-col items-start gap-1.5 p-3 rounded-[10px] border text-left transition-colors relative ${selected === s.id ? 'bg-[var(--surface)] border-[var(--border-soft)]' : 'bg-[var(--bg)] border-[var(--border-faint)] hover:border-[var(--border-soft)]'}`}
              >
                {!s.available && (
                  <span className="absolute top-2 right-2 text-[9px] font-mono tracking-widest uppercase text-[var(--text-dim)] bg-[var(--surface-2)] px-1.5 py-0.5 rounded-[3px]">soon</span>
                )}
                <span className="text-[20px]">{s.icon}</span>
                <span className="text-[13px] font-medium text-[var(--text)]">{s.name}</span>
                <span className="text-[11px] text-[var(--text-faint)]">{s.desc}</span>
              </button>
            ))}
          </div>

          {/* Config for selected source */}
          {selected === 'website' && (
            <div className="mt-4 flex flex-col gap-2">
              <label className="text-[12px] font-semibold text-[var(--text-mute)]">URL to crawl</label>
              <input type="url" value={urlInput} onChange={e => setUrlInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleConnect()}
                placeholder="https://docs.example.com"
                className="h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] font-mono text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors" />
            </div>
          )}

          {selected && selected !== 'website' && !SOURCES.find(s => s.id === selected)?.available && (
            <div className="mt-4 flex items-center gap-2 px-4 py-3 bg-[var(--surface)] border border-[var(--border-faint)] rounded-[10px]">
              <Icons.Activity style={{ width: 13, height: 13, color: 'var(--text-faint)' }} />
              <span className="text-[12.5px] text-[var(--text-faint)]">
                {SOURCES.find(s => s.id === selected)?.name} connector is coming soon. You'll be notified when it's available.
              </span>
            </div>
          )}
        </div>

        <div className="px-5 py-4 border-t border-[var(--border-faint)] shrink-0 flex items-center justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors">
            Cancel
          </button>
          <button
            onClick={handleConnect}
            disabled={!selected || connecting || (selected === 'website' && !urlInput.trim())}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--accent)] text-white text-[13px] font-medium border-none cursor-pointer hover:brightness-110 transition-colors disabled:opacity-40 disabled:cursor-default"
          >
            <Icons.Plug style={{ width: 13, height: 13 }} />
            {connecting ? 'Connecting…' : 'Connect'}
          </button>
        </div>
      </div>
    </>,
    document.body
  )
}

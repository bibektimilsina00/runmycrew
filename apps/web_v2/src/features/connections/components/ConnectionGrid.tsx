import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useToast, useConfirm } from '@/shared/components'
import { useDeleteCredential, useRenameCredential } from '../hooks/useConnections'
import { credentialStatus } from '../types/connectionsTypes'
import type { Credential, Provider } from '../types/connectionsTypes'

interface Props {
  credentials: Credential[]
  providers: Provider[]
  canManage?: boolean
}

const STATUS_LABEL = { ok: 'Connected', warn: 'Expiring soon', err: 'Auth failed' }
const STATUS_COLOR = {
  ok:   'bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]',
  warn: 'bg-[oklch(0.82_0.14_80/0.16)] text-[var(--warn)]',
  err:  'bg-[oklch(0.70_0.18_22/0.16)] text-[var(--err)]',
}

export function ConnectionGrid({ credentials, providers, canManage = true }: Props) {
  const { toast } = useToast()
  const confirm = useConfirm()
  const deleteCredential = useDeleteCredential()
  const renameCredential = useRenameCredential()

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')

  const providerMap = Object.fromEntries(providers.map(p => [p.id, p]))

  const handleDelete = async (id: string, name: string) => {
    const ok = await confirm({
      title: 'Disconnect integration',
      message: `Disconnect "${name}"? Workflows using this connection will stop working.`,
      confirmText: 'Disconnect',
      variant: 'danger',
    })
    if (!ok) return
    deleteCredential.mutate(id, {
      onSuccess: () => toast('Disconnected', { variant: 'ok', description: `${name} has been removed.` }),
      onError: (e) => toast('Failed', { variant: 'err', description: e instanceof Error ? e.message : 'Try again.' }),
    })
  }

  const handleRename = async (id: string) => {
    if (!editName.trim()) { setEditingId(null); return }
    await renameCredential.mutateAsync({ id, name: editName.trim() })
    toast('Renamed', { variant: 'ok' })
    setEditingId(null)
  }

  if (credentials.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-[var(--text-faint)]">
        <Icons.Plug style={{ width: 24, height: 24, color: 'var(--text-dim)' }} />
        <span className="text-[13px]">No connections yet. Click "Add connection" to get started.</span>
      </div>
    )
  }

  return (
    <div className="conn-grid">
      {credentials.map(cred => {
        const provider = providerMap[cred.type]
        const status   = credentialStatus(cred)
        const initial  = (provider?.name ?? cred.name).slice(0, 2).toUpperCase()
        const isEditing = editingId === cred.id
        const connectedDate = new Date(cred.created_at).toLocaleDateString('en-US', {
          month: 'short', day: 'numeric', year: 'numeric',
        })

        return (
          <div key={cred.id} className="conn-card group">
            <div className="conn-card-head">
              {provider?.icon_url ? (
                <img
                  src={provider.icon_url}
                  alt={provider.name}
                  className="w-[34px] h-[34px] rounded-[8px] object-contain bg-[var(--surface)] p-1"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                />
              ) : (
                <span className="conn-icon" style={{ width: 34, height: 34, borderRadius: 8, fontSize: 12.5 }}>
                  {initial}
                </span>
              )}
              <div className="flex items-center gap-2 ml-auto">
                <span className={`font-mono text-[9.5px] font-semibold tracking-widest uppercase px-[7px] py-[3px] pb-[2px] rounded-[4px] ${STATUS_COLOR[status]}`}>
                  {STATUS_LABEL[status]}
                </span>
              </div>
            </div>

            <div className="conn-card-body">
              {isEditing ? (
                <input
                  autoFocus
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleRename(cred.id); if (e.key === 'Escape') setEditingId(null) }}
                  onBlur={() => handleRename(cred.id)}
                  className="conn-card-name bg-[var(--bg)] border border-[var(--border)] rounded-[6px] px-2 py-0.5 outline-none w-full text-[13px]"
                />
              ) : (
                <div
                  className={`conn-card-name ${canManage ? 'cursor-pointer hover:text-[var(--text)] transition-colors' : ''}`}
                  onDoubleClick={() => { if (canManage) { setEditingId(cred.id); setEditName(cred.name) } }}
                  title={canManage ? 'Double-click to rename' : undefined}
                >
                  {cred.name}
                </div>
              )}
              <div className="conn-card-sub">{provider?.description ?? cred.type}</div>
            </div>

            <div className="conn-card-foot">
              <span className="flex items-center gap-1 text-[var(--text-dim)]">
                <Icons.Clock style={{ width: 10, height: 10 }} />
                {connectedDate}
              </span>
              {canManage && (
                <button
                  onClick={() => handleDelete(cred.id, cred.name)}
                  className="opacity-0 group-hover:opacity-100 inline-flex items-center gap-1 text-[11px] font-medium text-[var(--text-dim)] hover:text-[var(--err)] transition-all"
                  title="Disconnect"
                >
                  <Icons.Trash style={{ width: 11, height: 11 }} />
                  Disconnect
                </button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

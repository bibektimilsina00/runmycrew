import { useState, useMemo } from 'react'
import { Icons } from '@/shared/components/icons'
import { useWorkspaceStore } from '@/features/workspaces'
import { useCredentials, useProviders } from '../hooks/useConnections'
import { ConnectionGrid } from '../components/ConnectionGrid'
import { ConnectModal } from '../components/ConnectModal'
import { AuditLogPanel } from '../components/AuditLogPanel'
import { credentialStatus } from '../types/connectionsTypes'

export function Connections() {
  const { data: credentials = [], isLoading: loadingCreds } = useCredentials()
  const { data: providers  = [], isLoading: loadingProviders } = useProviders()
  const canManage = useWorkspaceStore(s => s.canManageMembers())

  const [search, setSearch]     = useState('')
  const [filter, setFilter]     = useState<'all' | 'oauth' | 'api_key' | 'ok' | 'warn' | 'err'>('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [auditOpen, setAuditOpen] = useState(false)

  const providerMap = useMemo(
    () => Object.fromEntries(providers.map(p => [p.id, p])),
    [providers]
  )

  const filtered = useMemo(() => credentials.filter(c => {
    const provider = providerMap[c.type]
    const status = credentialStatus(c)
    if (filter === 'oauth'   && provider?.type !== 'oauth')   return false
    if (filter === 'api_key' && provider?.type !== 'api_key') return false
    if (filter === 'ok'   && status !== 'ok')   return false
    if (filter === 'warn' && status !== 'warn') return false
    if (filter === 'err'  && status !== 'err')  return false
    if (search.trim()) {
      const q = search.toLowerCase()
      return (
        c.name.toLowerCase().includes(q) ||
        (provider?.name ?? '').toLowerCase().includes(q) ||
        (provider?.description ?? '').toLowerCase().includes(q)
      )
    }
    return true
  }), [credentials, providerMap, filter, search])

  const counts = useMemo(() => ({
    all:     credentials.length,
    oauth:   credentials.filter(c => providerMap[c.type]?.type === 'oauth').length,
    api_key: credentials.filter(c => providerMap[c.type]?.type === 'api_key').length,
    ok:      credentials.filter(c => credentialStatus(c) === 'ok').length,
    warn:    credentials.filter(c => credentialStatus(c) === 'warn').length,
    err:     credentials.filter(c => credentialStatus(c) === 'err').length,
  }), [credentials, providerMap])

  const isLoading = loadingCreds || loadingProviders

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · {credentials.length} connected</span>
          <h1>Connections</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={() => setAuditOpen(true)}>
            <Icons.Activity /> Audit log
          </button>
          {canManage && (
            <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
              <Icons.Plus /> Add connection
            </button>
          )}
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {([
            ['all',     'All'],
            ['oauth',   'OAuth'],
            ['api_key', 'API Key'],
            ['err',     'Errors'],
            ['warn',    'Expiring'],
          ] as const).map(([id, label]) => (
            counts[id] > 0 || id === 'all' ? (
              <button
                key={id}
                className={`filter-tab${filter === id ? ' active' : ''}`}
                onClick={() => setFilter(id)}
              >
                {label}
                <span className="filter-count">{counts[id]}</span>
              </button>
            ) : null
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input
              placeholder="Search connections"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
          <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
          Loading connections…
        </div>
      ) : (
        <ConnectionGrid credentials={filtered} providers={providers} canManage={canManage} />
      )}

      {modalOpen && (
        <ConnectModal
          providers={providers}
          onClose={() => setModalOpen(false)}
        />
      )}

      {auditOpen && (
        <AuditLogPanel
          providers={providers}
          onClose={() => setAuditOpen(false)}
        />
      )}
    </div>
  )
}

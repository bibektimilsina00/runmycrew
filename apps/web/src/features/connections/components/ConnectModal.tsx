import { useState } from 'react'
import { createPortal } from 'react-dom'
import { Icons } from '@/shared/components/icons'
import { useToast } from '@/shared/components'
import { useCreateCredential, useOAuthUrl } from '../hooks/useConnections'
import type { Provider } from '../types/connectionsTypes'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'

interface Props {
  providers: Provider[]
  onClose: () => void
  /** Preselect a provider by id, skipping the browse step. */
  initialProviderId?: string
  /** Fires after credential is created (api_key flow). Receives the created credential id when available. */
  onCreated?: (credentialId?: string) => void
}

function ProviderTile({ p, onClick }: { p: Provider; onClick: (p: Provider) => void }) {
  return (
    <button
      onClick={() => onClick(p)}
      className="flex items-center gap-3 px-4 py-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px] text-left hover:border-[var(--border-soft)] hover:bg-[var(--surface)] transition-all group"
    >
      {p.icon_slug ? (
        <div
          className="flex w-[32px] h-[32px] shrink-0 items-center justify-center rounded-[7px] p-1 [&_img]:h-[22px] [&_img]:w-[22px] [&_img]:object-contain"
          style={{ background: p.color ?? 'var(--surface)' }}
        >
          <BrandIcon slug={p.icon_slug} />
        </div>
      ) : (
        <span className="w-[32px] h-[32px] rounded-[7px] bg-[var(--surface-2)] flex items-center justify-center text-[11px] font-bold text-[var(--text)] shrink-0">
          {p.name.slice(0, 2).toUpperCase()}
        </span>
      )}
      <span className="flex flex-col gap-0.5 min-w-0">
        <span className="text-[13px] font-medium text-[var(--text)] truncate">{p.name}</span>
        <span className="text-[10.5px] font-mono text-[var(--text-faint)] uppercase tracking-widest">
          {p.type === 'oauth' ? 'OAuth' : 'API Key'}
        </span>
      </span>
      <Icons.CaretRight style={{ width: 12, height: 12, color: 'var(--text-dim)', flexShrink: 0, marginLeft: 'auto', opacity: 0 }} className="group-hover:opacity-100 transition-opacity" />
    </button>
  )
}

export function ConnectModal({ providers, onClose, initialProviderId, onCreated }: Props) {
  const { toast } = useToast()
  const createCredential = useCreateCredential()
  const getOAuthUrl = useOAuthUrl()

  const initial = initialProviderId
    ? providers.find(p => p.id === initialProviderId) ?? null
    : null

  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'oauth' | 'api_key'>('all')
  const [selected, setSelected] = useState<Provider | null>(initial)
  const [openBrand, setOpenBrand] = useState<string | null>(null)
  const [connName, setConnName] = useState(initial?.name ?? '')
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [connecting, setConnecting] = useState(false)

  const filtered = providers.filter(p => {
    if (typeFilter !== 'all' && p.type !== typeFilter) return false
    if (search.trim()) {
      const q = search.toLowerCase()
      return p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q)
    }
    return true
  })

  // Collapse per-service providers under one brand tile. A brand tile
  // acts like a folder — clicking opens the brand's inner list. When
  // the user searches, the brand grouping stays but auto-opens every
  // brand that has a matching child so results stay visible.
  const brandMap = new Map<string, Provider[]>()
  const flat: Provider[] = []
  for (const p of filtered) {
    if (p.brand) {
      const list = brandMap.get(p.brand) ?? []
      list.push(p)
      brandMap.set(p.brand, list)
    } else {
      flat.push(p)
    }
  }
  const searching = search.trim().length > 0
  const brandGroups = Array.from(brandMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([brand, providers]) => ({ brand, providers }))

  const BRAND_LABEL: Record<string, string> = {
    google: 'Google', aws: 'AWS', microsoft: 'Microsoft',
    atlassian: 'Atlassian', twilio: 'Twilio', sap: 'SAP',
    meta: 'Meta', ai: 'AI',
  }

  const handleSelectProvider = (p: Provider) => {
    setSelected(p)
    setConnName(p.name)
    setFieldValues({})
  }

  const handleConnect = async () => {
    if (!selected) return
    setConnecting(true)
    try {
      if (selected.type === 'oauth') {
        const { url } = await getOAuthUrl.mutateAsync({
          service: selected.id.replace('_oauth', ''),
          name: connName || selected.name,
        })
        // Remember the route the user started from so `/oauth/return`
        // can bounce them back after the callback. Without this the
        // backend's fallback redirect (`/settings/integrations`) hits
        // the catch-all and dumps them on the dashboard.
        try {
          sessionStorage.setItem(
            'oauth_return_to',
            window.location.pathname + window.location.search + window.location.hash,
          )
        } catch { /* private-mode: silently fall back to dashboard */ }
        window.location.href = url
        return
      }

      // API key
      const data: Record<string, string> = {}
      for (const field of (selected.fields ?? [])) {
        data[field.id] = fieldValues[field.id] ?? ''
      }
      const created = await createCredential.mutateAsync({ name: connName || selected.name, type: selected.id, data })
      toast('Connected', { variant: 'ok', description: `${selected.name} has been connected.` })
      onCreated?.(created?.id)
      onClose()
    } catch (err) {
      toast('Failed to connect', { variant: 'err', description: err instanceof Error ? err.message : 'Try again.' })
    } finally {
      setConnecting(false)
    }
  }

  const canSubmit = selected && connName.trim() && (
    selected.type === 'oauth' ||
    (selected.fields ?? []).every(f => (fieldValues[f.id] ?? '').trim())
  )

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[92vw] max-w-[1280px] h-[92vh] bg-[var(--bg-2)] border border-[var(--border)] rounded-[10px] flex flex-col shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-faint)]">
          <div>
            <h3 className="text-[15px] font-semibold text-[var(--text)] tracking-tight">
              {selected ? `Connect ${selected.name}` : 'Add connection'}
            </h3>
            {selected && (
              <button onClick={() => setSelected(null)} className="text-[12px] text-[var(--text-faint)] hover:text-[var(--text)] transition-colors mt-0.5">
                ← Back to providers
              </button>
            )}
          </div>
          <button onClick={onClose} className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]">✕</button>
        </div>

        {!selected ? (
          <>
            {/* Search + filter */}
            <div className="px-5 pt-4 pb-3 flex items-center gap-3 border-b border-[var(--border-faint)]">
              <div className="flex items-center gap-2 flex-1 h-[34px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] focus-within:border-[var(--border)] transition-colors">
                <Icons.Search style={{ width: 13, height: 13, color: 'var(--text-faint)', flexShrink: 0 }} />
                <input
                  autoFocus
                  type="text"
                  placeholder="Search integrations…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="flex-1 bg-transparent border-none outline-none text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)]"
                />
              </div>
              <div className="flex items-center bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] p-[3px] gap-[2px]">
                {(['all', 'oauth', 'api_key'] as const).map(t => (
                  <button
                    key={t}
                    onClick={() => setTypeFilter(t)}
                    className={`px-3 py-1 rounded-[6px] text-[12px] font-medium capitalize transition-colors ${typeFilter === t ? 'bg-[var(--surface)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]' : 'text-[var(--text-mute)] hover:text-[var(--text)]'}`}
                  >
                    {t === 'api_key' ? 'API Key' : t === 'oauth' ? 'OAuth' : 'All'}
                  </button>
                ))}
              </div>
            </div>

            {/* Provider grid */}
            <div className="overflow-y-auto flex-1 p-5">
              {filtered.length === 0 ? (
                <div className="flex flex-col items-center gap-2 py-8 text-[var(--text-faint)]">
                  <Icons.Search style={{ width: 18, height: 18, color: 'var(--text-dim)' }} />
                  <span className="text-[13px]">No integrations match "{search}"</span>
                </div>
              ) : (
                <div className="grid grid-cols-4 gap-2">
                  {flat.map(p => (
                    <ProviderTile key={p.id} p={p} onClick={handleSelectProvider} />
                  ))}
                  {brandGroups.map(({ brand, providers: kids }) => {
                    const isOpen = openBrand === brand || searching
                    // Brand tile shows the brand icon + count. When open,
                    // the children render below in a nested full-width row.
                    return (
                      <div key={brand} className={isOpen ? 'col-span-4' : ''}>
                        <button
                          onClick={() => setOpenBrand(o => o === brand ? null : brand)}
                          className="w-full flex items-center gap-3 px-4 py-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px] text-left hover:border-[var(--border-soft)] hover:bg-[var(--surface)] transition-all"
                        >
                          <div className="flex w-[32px] h-[32px] shrink-0 items-center justify-center rounded-[7px] p-1 bg-[var(--surface-2)] [&_img]:h-[22px] [&_img]:w-[22px] [&_img]:object-contain">
                            <BrandIcon slug={brand} />
                          </div>
                          <span className="flex flex-col gap-0.5 min-w-0 flex-1">
                            <span className="text-[13px] font-medium text-[var(--text)] truncate">{BRAND_LABEL[brand] ?? brand}</span>
                            <span className="text-[10.5px] font-mono text-[var(--text-faint)] uppercase tracking-widest">
                              {kids.length} service{kids.length === 1 ? '' : 's'}
                            </span>
                          </span>
                          <span className={`shrink-0 text-[10px] text-[var(--text-dim)] transition-transform ${isOpen ? 'rotate-90' : ''}`}>▶</span>
                        </button>
                        {isOpen && (
                          <div className="mt-2 grid grid-cols-4 gap-2 border-l-2 border-[var(--border-faint)] pl-3 ml-2">
                            {kids.map(p => (
                              <ProviderTile key={p.id} p={p} onClick={handleSelectProvider} />
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </>
        ) : (
          /* Connect form — content scrolls; the Cancel/Connect row is
             pinned to the modal's bottom so users always see the
             primary action, no matter how many scope items render. */
          <div className="flex min-h-0 flex-1 flex-col">
            <div className="min-h-0 flex-1 overflow-y-auto p-6 flex flex-col gap-5">
            {/* Provider info */}
            <div className="flex items-center gap-3 p-4 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px]">
              {selected.icon_slug && (
                <div
                  className="flex w-[40px] h-[40px] shrink-0 items-center justify-center rounded-[9px] p-1.5 [&_img]:h-[26px] [&_img]:w-[26px] [&_img]:object-contain"
                  style={{ background: selected.color ?? 'var(--surface)' }}
                >
                  <BrandIcon slug={selected.icon_slug} />
                </div>
              )}
              <div className="flex flex-col gap-0.5">
                <span className="text-[13.5px] font-semibold text-[var(--text)]">{selected.name}</span>
                <span className="text-[12px] text-[var(--text-faint)]">{selected.description}</span>
              </div>
              <span className={`ml-auto shrink-0 font-mono text-[9.5px] font-semibold tracking-widest uppercase px-[8px] py-[3px] rounded-[4px] ${selected.type === 'oauth' ? 'bg-[oklch(0.78_0.13_245/0.14)] text-[var(--accent)]' : 'bg-[var(--surface-2)] text-[var(--text-mute)]'}`}>
                {selected.type === 'oauth' ? 'OAuth 2.0' : 'API Key'}
              </span>
            </div>

            {/* OAuth scopes */}
            {selected.type === 'oauth' && selected.scopes && selected.scopes.length > 0 && (
              <div className="flex flex-col gap-2">
                <span className="text-[11.5px] font-medium text-[var(--text-mute)]">Permissions requested</span>
                <div className="flex flex-col gap-1.5">
                  {selected.scopes.map((s, i) => (
                    <div key={i} className="flex items-center gap-2 text-[12.5px] text-[var(--text-mute)]">
                      <Icons.Check style={{ width: 12, height: 12, color: 'var(--ok)', flexShrink: 0 }} />
                      {s}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Connection name */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[11.5px] font-medium text-[var(--text-mute)]">Connection name</label>
              <input
                type="text"
                value={connName}
                onChange={e => setConnName(e.target.value)}
                placeholder={selected.name}
                className="h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors"
              />
            </div>

            {/* API key fields */}
            {selected.type === 'api_key' && (selected.fields ?? []).map(field => (
              <div key={field.id} className="flex flex-col gap-1.5">
                <label className="text-[11.5px] font-medium text-[var(--text-mute)]">{field.label}</label>
                {selected.hint && <p className="text-[11px] text-[var(--text-dim)] font-mono">Format: {selected.hint}</p>}
                <input
                  type={field.type === 'password' ? 'password' : 'text'}
                  value={fieldValues[field.id] ?? ''}
                  onChange={e => setFieldValues(v => ({ ...v, [field.id]: e.target.value }))}
                  placeholder={field.placeholder}
                  className="h-[38px] px-3 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[9px] text-[13px] font-mono text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none focus:border-[var(--border)] transition-colors"
                />
              </div>
            ))}

            </div>
            {/* Pinned footer */}
            <div className="shrink-0 flex items-center justify-end gap-3 px-6 py-4 border-t border-[var(--border-faint)] bg-[var(--bg-2)]">
              <button onClick={onClose} className="px-4 py-2 rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors">
                Cancel
              </button>
              <button
                onClick={handleConnect}
                disabled={!canSubmit || connecting}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--accent)] text-white text-[13px] font-medium border-none cursor-pointer hover:brightness-110 transition-colors disabled:opacity-40 disabled:cursor-default"
              >
                {connecting ? (
                  <><div className="w-[12px] h-[12px] border-2 border-[var(--bg)] border-t-transparent rounded-full animate-spin" /> Connecting…</>
                ) : selected.type === 'oauth' ? (
                  <><Icons.Plug style={{ width: 13, height: 13 }} /> Connect with OAuth</>
                ) : (
                  <><Icons.Check style={{ width: 13, height: 13 }} /> Save connection</>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </>,
    document.body
  )
}

import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Loader2, Search, X } from 'lucide-react'
import { useWorkspaceStore } from '@/features/workspaces'
import { useCredentials, useProviders } from '../hooks/useConnections'
import { ConnectModal } from '../components/ConnectModal'
import { AuditLogPanel } from '../components/AuditLogPanel'
import { credentialStatus, type Provider, type Credential } from '../types/connectionsTypes'
import { BrandIcon } from '@/features/workflow-editor/utils/BrandIcon'
import { cn } from '@/lib/cn'

type FilterId = 'all' | 'oauth' | 'api_key'

const FILTERS: { id: FilterId; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'oauth', label: 'OAuth' },
  { id: 'api_key', label: 'API Key' },
]

/**
 * Categorises a provider onto a section by its id / brand. Hand-rolled so
 * we don't need a backend category field — everything falls back to
 * "Other" if none of the buckets match.
 */
function providerCategory(p: Provider): string {
  const id = p.id.toLowerCase()
  const brand = (p.brand ?? '').toLowerCase()
  if (id.startsWith('ai_') || id.includes('openai') || id.includes('anthropic') || id.includes('llm') || id.includes('cohere') || id.includes('mistral') || id.includes('perplexity') || id.includes('gemini') || id.includes('elevenlabs') || id.includes('huggingface') || id.includes('replicate') || id.includes('groq'))
    return 'AI'
  if (id.includes('slack') || id.includes('discord') || id.includes('teams') || id.includes('telegram') || id.includes('twilio') || id.includes('whatsapp') || id.includes('email') || id.includes('sms') || id.includes('sendgrid') || id.includes('mailgun') || id.includes('resend'))
    return 'Communication'
  if (id.includes('google') || brand === 'google' || id === 'gmail' || id.startsWith('g_') || id.includes('gdrive') || id.includes('gsheet') || id.includes('gcal') || id.includes('gdoc') || id.includes('notion') || id.includes('airtable') || id.includes('coda') || id.includes('confluence') || id.includes('office365') || id.includes('excel') || id.includes('outlook'))
    return 'Productivity'
  if (id.includes('salesforce') || id.includes('hubspot') || id.includes('pipedrive') || id.includes('intercom') || id.includes('zendesk') || id.includes('shopify') || id.includes('stripe') || id.includes('paypal'))
    return 'Business'
  if (id.includes('github') || id.includes('gitlab') || id.includes('bitbucket') || id.includes('linear') || id.includes('jira') || id.includes('asana') || id.includes('trello') || id.includes('clickup') || id.includes('monday'))
    return 'Developer'
  if (id.includes('s3') || id.includes('aws') || id.includes('gcs') || id.includes('dropbox') || id.includes('box') || id.includes('onedrive'))
    return 'Storage'
  if (id.includes('database') || id.includes('postgres') || id.includes('mysql') || id.includes('mongodb') || id.includes('redis') || id.includes('supabase'))
    return 'Databases'
  return 'Other'
}

const SECTION_ORDER = [
  'Featured',
  'AI',
  'Communication',
  'Productivity',
  'Business',
  'Developer',
  'Storage',
  'Databases',
  'Other',
]

const FEATURED_IDS = new Set([
  'slack', 'gmail', 'jira', 'github', 'google_sheets', 'hubspot',
  'notion', 'openai', 'anthropic',
])

export function Connections() {
  const { data: credentials = [], isLoading: loadingCreds } = useCredentials()
  const { data: providers = [], isLoading: loadingProviders } = useProviders()
  const canManage = useWorkspaceStore(s => s.canManageMembers())
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<FilterId>('all')
  const [modalProviderId, setModalProviderId] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [auditOpen, setAuditOpen] = useState(false)

  const providerMap = useMemo(
    () => Object.fromEntries(providers.map(p => [p.id, p])),
    [providers],
  )

  const filteredProviders = useMemo(() => {
    const q = search.trim().toLowerCase()
    return providers.filter(p => {
      if (filter === 'oauth' && p.type !== 'oauth') return false
      if (filter === 'api_key' && p.type !== 'api_key') return false
      if (!q) return true
      return (
        p.name.toLowerCase().includes(q) ||
        (p.description ?? '').toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q)
      )
    })
  }, [providers, filter, search])

  const featured = useMemo(
    () => filteredProviders.filter(p => FEATURED_IDS.has(p.id)).slice(0, 6),
    [filteredProviders],
  )

  const sectioned = useMemo(() => {
    const buckets: Record<string, Provider[]> = {}
    for (const p of filteredProviders) {
      const cat = providerCategory(p)
      if (!buckets[cat]) buckets[cat] = []
      buckets[cat].push(p)
    }
    return SECTION_ORDER
      .filter(k => k !== 'Featured' && buckets[k]?.length)
      .map(k => ({ name: k, items: buckets[k].sort((a, b) => a.name.localeCompare(b.name)) }))
  }, [filteredProviders])

  const filteredCredentials = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return credentials
    return credentials.filter(c => {
      const provider = providerMap[c.type]
      return (
        c.name.toLowerCase().includes(q) ||
        (provider?.name ?? '').toLowerCase().includes(q)
      )
    })
  }, [credentials, providerMap, search])

  const isLoading = loadingCreds || loadingProviders

  const openConnect = (providerId?: string) => {
    setModalProviderId(providerId ?? null)
    setModalOpen(true)
  }

  return (
    <div className="flex h-full flex-col">
      {/* ── Top tabs ────────────────────────────────────── */}
      <div className="flex items-center gap-4 border-b border-border-faint px-8 pt-4">
        <button
          className="border-b-2 border-text px-1 pb-3 text-[13.5px] font-semibold text-text"
          disabled
        >
          Integrations
        </button>
        <button
          onClick={() => navigate('/skills')}
          className="border-b-2 border-transparent px-1 pb-3 text-[13.5px] font-medium text-text-mute hover:text-text"
        >
          Skills
        </button>

        <div className="ml-auto flex items-center gap-2 pb-2">
          <button
            onClick={() => setAuditOpen(true)}
            className="rounded-[7px] border border-border-faint bg-bg2 px-3 py-1.5 text-[12px] font-medium text-text-mute hover:border-border hover:text-text"
          >
            Audit log
          </button>
          {canManage && (
            <button
              onClick={() => openConnect()}
              className="rounded-[7px] px-3 py-1.5 text-[12px] font-medium text-white hover:brightness-110"
              style={{ background: 'var(--accent, #8b5cf6)' }}
            >
              + Add integration
            </button>
          )}
        </div>
      </div>

      {/* ── Scrollable body ─────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mx-auto flex max-w-[1080px] flex-col gap-6">
          {/* Hero collage */}
          <HeroCollage providers={providers} onExplore={() => openConnect()} />

          {/* Search + filter */}
          <div className="flex items-center gap-3">
            <div className="flex h-10 flex-1 items-center gap-2 rounded-[10px] border border-border-faint bg-bg2 px-3">
              <Search size={14} className="shrink-0 text-text-faint" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search integrations…"
                className="flex-1 bg-transparent text-[13px] text-text outline-none placeholder:text-text-faint"
              />
              {search && (
                <button onClick={() => setSearch('')} className="text-text-faint hover:text-text">
                  <X size={12} />
                </button>
              )}
            </div>
            <div className="flex items-center gap-1 rounded-[10px] border border-border-faint bg-bg2 p-1">
              {FILTERS.map(f => (
                <button
                  key={f.id}
                  onClick={() => setFilter(f.id)}
                  className={cn(
                    'rounded-[7px] px-3 py-1.5 text-[12px] font-medium transition',
                    filter === f.id
                      ? 'bg-surface text-text'
                      : 'text-text-mute hover:text-text',
                  )}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {isLoading ? (
            <div className="flex items-center gap-2 py-8 text-[13px] text-text-faint">
              <Loader2 size={14} className="animate-spin" />
              Loading integrations…
            </div>
          ) : (
            <div className="flex flex-col gap-8">
              {/* Connected */}
              {filteredCredentials.length > 0 && (
                <Section title="Connected">
                  <div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
                    {filteredCredentials.map(c => (
                      <ConnectedCard
                        key={c.id}
                        credential={c}
                        provider={providerMap[c.type]}
                        onOpen={() => openConnect(c.type)}
                      />
                    ))}
                  </div>
                </Section>
              )}

              {/* Featured */}
              {featured.length > 0 && !search && (
                <Section title="Featured">
                  <div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
                    {featured.map(p => (
                      <ProviderCard key={p.id} provider={p} onOpen={() => openConnect(p.id)} />
                    ))}
                  </div>
                </Section>
              )}

              {/* Categorised */}
              {sectioned.map(sec => (
                <Section key={sec.name} title={sec.name}>
                  <div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
                    {sec.items.map(p => (
                      <ProviderCard key={p.id} provider={p} onOpen={() => openConnect(p.id)} />
                    ))}
                  </div>
                </Section>
              ))}

              {filteredProviders.length === 0 && (
                <p className="rounded-[10px] border border-dashed border-border-faint bg-bg2 p-8 text-center text-[13px] text-text-faint">
                  No integrations match &ldquo;{search}&rdquo;.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {modalOpen && (
        <ConnectModal
          providers={providers}
          initialProviderId={modalProviderId ?? undefined}
          onClose={() => {
            setModalOpen(false)
            setModalProviderId(null)
          }}
        />
      )}

      {auditOpen && (
        <AuditLogPanel providers={providers} onClose={() => setAuditOpen(false)} />
      )}
    </div>
  )
}

/* ─────────────────────────────────────────────────────────── */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-[11px] font-semibold uppercase tracking-wider text-text-mute">
        {title}
      </h2>
      {children}
    </section>
  )
}

function ProviderCard({ provider, onOpen }: { provider: Provider; onOpen: () => void }) {
  return (
    <button
      onClick={onOpen}
      className="group flex items-center gap-3 rounded-[11px] border border-border-faint bg-bg2 px-4 py-3 text-left transition-colors hover:border-border hover:bg-bg2/80"
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-[8px] bg-bg [&_img]:h-6 [&_img]:w-6 [&_img]:object-contain">
        {provider.icon_slug ? <BrandIcon slug={provider.icon_slug} /> : (
          <span className="text-[13px] font-semibold text-text-mute">{provider.name[0]}</span>
        )}
      </span>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13.5px] font-semibold text-text">{provider.name}</div>
        <div className="truncate text-[11.5px] text-text-mute">
          {provider.description || (provider.type === 'oauth' ? 'OAuth connection' : 'API key connection')}
        </div>
      </div>
      <ArrowRight size={14} className="text-text-faint transition group-hover:translate-x-0.5 group-hover:text-text" />
    </button>
  )
}

function ConnectedCard({
  credential, provider, onOpen,
}: { credential: Credential; provider?: Provider; onOpen: () => void }) {
  const status = credentialStatus(credential)
  return (
    <button
      onClick={onOpen}
      className="group flex items-center gap-3 rounded-[11px] border border-border-faint bg-bg2 px-4 py-3 text-left transition-colors hover:border-border"
    >
      <span className="relative flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-[8px] bg-bg [&_img]:h-6 [&_img]:w-6 [&_img]:object-contain">
        {provider?.icon_slug ? <BrandIcon slug={provider.icon_slug} /> : (
          <span className="text-[13px] font-semibold text-text-mute">{(provider?.name ?? '?')[0]}</span>
        )}
        <span
          className={cn(
            'absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-bg2',
            status === 'ok'   && 'bg-[var(--ok)]',
            status === 'warn' && 'bg-[var(--warn)]',
            status === 'err'  && 'bg-[var(--err)]',
          )}
        />
      </span>
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13.5px] font-semibold text-text">{credential.name}</div>
        <div className="truncate text-[11.5px] text-text-mute">
          {provider?.name ?? credential.type} · {status === 'ok' ? 'Connected' : status === 'warn' ? 'Expiring soon' : 'Reauth needed'}
        </div>
      </div>
      <ArrowRight size={14} className="text-text-faint transition group-hover:translate-x-0.5 group-hover:text-text" />
    </button>
  )
}

function HeroCollage({ providers, onExplore }: { providers: Provider[]; onExplore: () => void }) {
  const withIcons = providers.filter(p => p.icon_slug).slice(0, 14)
  return (
    <div className="relative overflow-hidden rounded-[14px] border border-border-faint bg-[radial-gradient(circle_at_top,rgba(139,92,246,0.10),transparent_70%)] bg-bg2 px-5 py-4">
      <div className="grid grid-cols-7 gap-3">
        {withIcons.map(p => (
          <div
            key={p.id}
            className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-[7px] bg-bg [&_img]:h-6 [&_img]:w-6 [&_img]:object-contain"
            title={p.name}
          >
            <BrandIcon slug={p.icon_slug as string} />
          </div>
        ))}
      </div>
      <button
        onClick={onExplore}
        className="absolute bottom-3 right-3 flex items-center gap-1 rounded-[7px] border border-border-faint bg-bg2 px-3 py-1.5 text-[11.5px] font-medium text-text-mute hover:border-border hover:text-text"
      >
        Add integration <ArrowRight size={11} />
      </button>
    </div>
  )
}

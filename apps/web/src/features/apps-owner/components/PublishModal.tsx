import { useMemo, useState } from 'react'
import { Check, Copy, ExternalLink, Globe, Loader2 } from 'lucide-react'
import { Button, Input, Modal, Textarea } from '@/shared/components'
import {
  usePublishApp,
  useUnpublishApp,
  useWorkflowApp,
  useWorkflowAppVersions,
  useRollbackApp,
  useResetApiKey,
} from '../hooks/useAppPublish'
import type { PublishAppRequest } from '../types/appsOwnerTypes'

interface PublishModalProps {
  open: boolean
  onClose: () => void
  workflowId: string
  workflowName: string
}

type Tab = 'general' | 'auth' | 'theme' | 'form' | 'advanced'

const TABS: { id: Tab; label: string }[] = [
  { id: 'general', label: 'General' },
  { id: 'auth', label: 'Auth' },
  { id: 'theme', label: 'Theme' },
  { id: 'form', label: 'Form' },
  { id: 'advanced', label: 'Advanced' },
]

const AUTH_MODES: { id: string; label: string; hint: string }[] = [
  { id: 'public', label: 'Public', hint: 'Anyone with the link.' },
  { id: 'password', label: 'Password', hint: 'One shared password.' },
  { id: 'login', label: 'Login required', hint: 'Visitors sign in with a Fuse account.' },
  { id: 'api_key', label: 'API key', hint: 'Callers send X-App-Key header. For embeds.' },
]

/**
 * Full publish surface — General / Auth / Theme / Form / Advanced tabs
 * with tabs beside a scrollable body. Post-publish shows share link +
 * version dropdown for rollback.
 */
export function PublishModal({ open, onClose, workflowId, workflowName }: PublishModalProps) {
  const current = useWorkflowApp(open ? workflowId : undefined)
  const versions = useWorkflowAppVersions(open ? workflowId : undefined)
  const publish = usePublishApp(workflowId)
  const unpublish = useUnpublishApp(workflowId)
  const rollback = useRollbackApp(workflowId)
  const resetKey = useResetApiKey(workflowId)

  const existing = current.data ?? null
  const [tab, setTab] = useState<Tab>('general')

  const initial = useMemo<PublishAppRequest>(() => ({
    title: existing?.title ?? workflowName,
    app_slug: existing?.app_slug ?? '',
    description: existing?.description ?? '',
    mode: existing?.mode ?? 'chat',
    auth_mode: existing?.auth_mode ?? 'public',
    config: existing?.config ?? {},
  }), [existing, workflowName])

  const [form, setForm] = useState<PublishAppRequest>(initial)
  const [password, setPassword] = useState('')
  const [copied, setCopied] = useState(false)
  const [apiKey, setApiKey] = useState<string | null>(null)

  const cfg = (form.config ?? {}) as Record<string, unknown>
  const patch = <K extends keyof PublishAppRequest>(key: K, value: PublishAppRequest[K]) =>
    setForm(f => ({ ...f, [key]: value }))
  const patchCfg = (key: string, value: unknown) =>
    setForm(f => ({ ...f, config: { ...(f.config ?? {}), [key]: value } }))

  const busy = publish.isPending || unpublish.isPending || rollback.isPending
  const shareUrl = existing?.public_url ?? null

  const submit = () => {
    publish.mutate({
      title: form.title?.trim() || undefined,
      app_slug: form.app_slug?.trim() || undefined,
      description: form.description?.trim() || undefined,
      mode: form.mode || undefined,
      auth_mode: form.auth_mode || undefined,
      password: password.trim() || undefined,
      config: form.config,
    })
  }

  const copyLink = async () => {
    if (!shareUrl) return
    const abs = shareUrl.startsWith('http')
      ? shareUrl
      : new URL(shareUrl, window.location.origin).toString()
    try {
      await navigator.clipboard.writeText(abs)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* noop */
    }
  }

  const mintKey = async () => {
    try {
      const result = await resetKey.mutateAsync()
      setApiKey(result.api_key)
    } catch {
      /* noop */
    }
  }

  return (
    <Modal
      open={open}
      onClose={busy ? () => {} : onClose}
      title="Publish as app"
      description="Share this workflow as a hosted chat / form page. Graph is snapshotted so live edits don't affect the running app until you re-publish."
      width="880px"
      footer={
        <div className="flex w-full items-center justify-between gap-2">
          {existing ? (
            <button
              onClick={() => unpublish.mutate()}
              disabled={busy}
              className="text-[12px] text-[var(--err,#ef4444)] hover:underline disabled:opacity-40"
            >
              Unpublish
            </button>
          ) : (
            <span />
          )}
          <div className="flex gap-2">
            <Button variant="ghost" onClick={onClose} disabled={busy}>
              Close
            </Button>
            <Button onClick={submit} disabled={busy}>
              {publish.isPending
                ? 'Publishing…'
                : existing
                  ? 'Re-publish'
                  : 'Publish'}
            </Button>
          </div>
        </div>
      }
    >
      {/* Fixed-height grid so tab switches don't jump the modal size.
          Sidebar spans the full body height, body scrolls internally. */}
      <div className="grid h-[560px] grid-cols-[172px_1fr] gap-6">
        <nav className="flex flex-col gap-0.5 border-r border-border-faint pr-4">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={
                'rounded-[7px] px-3 py-2 text-left text-[13px] font-medium transition ' +
                (tab === t.id
                  ? 'bg-surface text-text shadow-[inset_0_0_0_1px_var(--border-soft)]'
                  : 'text-text-mute hover:bg-surface/60 hover:text-text')
              }
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="flex min-w-0 flex-col gap-4 overflow-y-auto pr-2">
          {current.isLoading && (
            <div className="flex items-center gap-2 text-[12.5px] text-text-mute">
              <Loader2 size={12} className="animate-spin" />
              Loading…
            </div>
          )}
          {existing && shareUrl && (
            <div className="flex items-center gap-2 rounded-[10px] border border-border-faint bg-bg2 p-3">
              <Globe size={14} className="text-accent" />
              <div className="min-w-0 flex-1">
                <div className="text-[11px] uppercase tracking-wider text-text-faint">
                  Live v{existing.version_num} · {existing.mode} · {existing.auth_mode}
                </div>
                <div className="truncate font-mono text-[12.5px] text-text">{shareUrl}</div>
              </div>
              <button onClick={copyLink} className="rounded-[6px] p-1.5 text-text-mute hover:bg-surface hover:text-text" title="Copy link">
                {copied ? <Check size={13} /> : <Copy size={13} />}
              </button>
              <a href={shareUrl} target="_blank" rel="noreferrer" className="rounded-[6px] p-1.5 text-text-mute hover:bg-surface hover:text-text" title="Open">
                <ExternalLink size={13} />
              </a>
            </div>
          )}

          {tab === 'general' && (
            <>
              <Field label="Title">
                <Input value={form.title ?? ''} onChange={e => patch('title', e.target.value)} placeholder="Support Bot" />
              </Field>
              <Field label="Slug" hint="URL-safe identifier. Leave blank to auto-generate.">
                <Input
                  value={form.app_slug ?? ''}
                  onChange={e => patch('app_slug', e.target.value.toLowerCase().replace(/[^a-z0-9-]+/g, '-'))}
                  placeholder="support-bot"
                />
              </Field>
              <Field label="Description">
                <Textarea value={form.description ?? ''} onChange={e => patch('description', e.target.value)} rows={2} />
              </Field>
              <Field label="Mode">
                <div className="flex gap-2">
                  {(['chat', 'form', 'agent'] as const).map(m => (
                    <button
                      key={m}
                      onClick={() => patch('mode', m)}
                      className={
                        'flex-1 rounded-[8px] border px-3 py-1.5 text-[12.5px] transition ' +
                        (form.mode === m
                          ? 'border-accent bg-accent/10 text-text'
                          : 'border-border-faint text-text-mute hover:border-border')
                      }
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </Field>
              {versions.data && versions.data.length > 1 && (
                <Field label="Rollback to earlier version">
                  <div className="flex flex-col gap-1.5">
                    {versions.data.map(v => (
                      <button
                        key={v.id}
                        disabled={busy || v.id === existing?.id}
                        onClick={() => rollback.mutate({ version_num: v.version_num })}
                        className="flex items-center justify-between rounded-[8px] border border-border-faint px-3 py-2 text-[12.5px] text-text-mute hover:border-border hover:text-text disabled:opacity-50"
                      >
                        <span>v{v.version_num} · {new Date(v.published_at).toLocaleString()}</span>
                        <span className="text-[11px]">{v.is_active ? 'Live' : 'Restore'}</span>
                      </button>
                    ))}
                  </div>
                </Field>
              )}
            </>
          )}

          {tab === 'auth' && (
            <>
              <Field label="Access">
                <div className="flex flex-col gap-1.5">
                  {AUTH_MODES.map(m => (
                    <button
                      key={m.id}
                      onClick={() => patch('auth_mode', m.id)}
                      className={
                        'flex flex-col items-start rounded-[9px] border px-3 py-2 text-left transition ' +
                        (form.auth_mode === m.id
                          ? 'border-accent bg-accent/10'
                          : 'border-border-faint hover:border-border')
                      }
                    >
                      <span className="text-[13px] font-medium text-text">{m.label}</span>
                      <span className="text-[11.5px] text-text-mute">{m.hint}</span>
                    </button>
                  ))}
                </div>
              </Field>
              {form.auth_mode === 'password' && (
                <Field label={existing?.password_hash ? 'New password (blank to keep)' : 'Password'}>
                  <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="min 6 chars" />
                </Field>
              )}
              {form.auth_mode === 'api_key' && existing && (
                <Field label="API key">
                  <div className="flex flex-col gap-2">
                    <Button variant="ghost" onClick={mintKey} disabled={resetKey.isPending}>
                      {resetKey.isPending ? 'Generating…' : existing.api_key_hash ? 'Rotate key' : 'Generate key'}
                    </Button>
                    {apiKey && (
                      <div className="rounded-[8px] border border-accent/50 bg-accent/10 p-2 text-[12px]">
                        <div className="mb-1 text-[10.5px] uppercase tracking-wider text-text-mute">Save this now — shown once</div>
                        <code className="break-all text-text">{apiKey}</code>
                      </div>
                    )}
                  </div>
                </Field>
              )}
              <Field label="Captcha (for public apps)">
                <Toggle value={!!cfg.captcha} onChange={v => patchCfg('captcha', v)} />
              </Field>
            </>
          )}

          {tab === 'theme' && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Primary color">
                  <Input type="color" value={String(cfg.primary_color ?? '#8b5cf6')} onChange={e => patchCfg('primary_color', e.target.value)} />
                </Field>
                <Field label="Dark mode">
                  <div className="flex gap-1.5">
                    {(['light', 'dark', 'auto'] as const).map(m => (
                      <button
                        key={m}
                        onClick={() => patchCfg('dark_mode', m)}
                        className={
                          'flex-1 rounded-[7px] border px-2 py-1.5 text-[12px] transition ' +
                          (cfg.dark_mode === m
                            ? 'border-accent bg-accent/10 text-text'
                            : 'border-border-faint text-text-mute hover:border-border')
                        }
                      >
                        {m}
                      </button>
                    ))}
                  </div>
                </Field>
              </div>
              <Field label="Logo URL">
                <Input value={String(cfg.logo_url ?? '')} onChange={e => patchCfg('logo_url', e.target.value)} placeholder="https://…/logo.svg" />
              </Field>
              <Field label="Welcome headline">
                <Input value={String(cfg.welcome_headline ?? '')} onChange={e => patchCfg('welcome_headline', e.target.value)} placeholder="How can I help you today?" />
              </Field>
              <Field label="Welcome subtitle">
                <Textarea rows={2} value={String(cfg.welcome_sub ?? '')} onChange={e => patchCfg('welcome_sub', e.target.value)} placeholder="Ask me anything." />
              </Field>
              <Field label="Show 'Powered by Fuse'">
                <Toggle value={cfg.show_powered_by !== false} onChange={v => patchCfg('show_powered_by', v)} />
              </Field>
            </>
          )}

          {tab === 'form' && (
            <div className="text-[13px] text-text-mute">
              Form fields are declared directly on the trigger.chat_app node — open its
              inspector to add, reorder, or edit inputs. The public form page renders
              whatever the node declares.
            </div>
          )}

          {tab === 'advanced' && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Rate limit (msgs/min per visitor)">
                  <Input
                    type="number"
                    min={1}
                    max={200}
                    value={Number(cfg.rate_limit_per_min ?? 20)}
                    onChange={e => patchCfg('rate_limit_per_min', Number(e.target.value))}
                  />
                </Field>
                <Field label="Session cost cap ($)">
                  <Input
                    type="number"
                    min={0}
                    step={0.5}
                    value={Number(cfg.session_cost_cap_usd ?? 5)}
                    onChange={e => patchCfg('session_cost_cap_usd', Number(e.target.value))}
                  />
                </Field>
                <Field label="Daily cost cap ($)">
                  <Input
                    type="number"
                    min={0}
                    step={1}
                    value={Number(cfg.daily_cost_cap_usd ?? 50)}
                    onChange={e => patchCfg('daily_cost_cap_usd', Number(e.target.value))}
                  />
                </Field>
                <Field label="Max file size (MB)">
                  <Input
                    type="number"
                    min={0}
                    value={Number(cfg.max_file_size_mb ?? 10)}
                    onChange={e => patchCfg('max_file_size_mb', Number(e.target.value))}
                  />
                </Field>
              </div>
              <Field label="Allow file upload">
                <Toggle value={!!cfg.allow_file_upload} onChange={v => patchCfg('allow_file_upload', v)} />
              </Field>
              <Field label="Allowed mime types (comma-sep, blank = any)">
                <Input
                  value={Array.isArray(cfg.allowed_file_types) ? (cfg.allowed_file_types as string[]).join(', ') : ''}
                  onChange={e =>
                    patchCfg(
                      'allowed_file_types',
                      e.target.value
                        .split(',')
                        .map(s => s.trim())
                        .filter(Boolean),
                    )
                  }
                  placeholder="image/png, image/jpeg, application/pdf"
                />
              </Field>
              <Field label="Allow message history">
                <Toggle value={cfg.allow_history !== false} onChange={v => patchCfg('allow_history', v)} />
              </Field>
              <Field label="Expires at (ISO date, blank = never)">
                <Input
                  type="datetime-local"
                  value={typeof cfg.expires_at === 'string' ? cfg.expires_at.slice(0, 16) : ''}
                  onChange={e => patchCfg('expires_at', e.target.value ? new Date(e.target.value).toISOString() : null)}
                />
              </Field>
            </>
          )}
        </div>
      </div>
    </Modal>
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[11px] font-medium uppercase tracking-wider text-text-mute">{label}</span>
      {children}
      {hint && <span className="text-[11px] text-text-faint">{hint}</span>}
    </label>
  )
}

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!value)}
      className={
        'relative inline-flex h-6 w-11 items-center rounded-full transition ' +
        (value ? 'bg-accent' : 'bg-surface')
      }
      aria-pressed={value}
    >
      <span
        className={
          'inline-block h-4 w-4 transform rounded-full bg-white transition ' +
          (value ? 'translate-x-6' : 'translate-x-1')
        }
      />
    </button>
  )
}

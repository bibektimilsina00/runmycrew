import { useMemo, useState } from 'react'
import { Check, Copy, ExternalLink, Globe, Loader2 } from 'lucide-react'
import { Button, Input, Modal, Textarea } from '@/shared/components'
import { usePublishApp, useUnpublishApp, useWorkflowApp } from '../hooks/useAppPublish'

interface PublishModalProps {
  open: boolean
  onClose: () => void
  workflowId: string
  workflowName: string
}

/**
 * PR-A modal: General tab only.
 *
 * Owner sees the current publish state (if any), can edit title / slug /
 * description, and hits Publish. Post-publish shows share URL + open link.
 * Auth / theme / form / advanced tabs land in PR-C.
 */
export function PublishModal({ open, onClose, workflowId, workflowName }: PublishModalProps) {
  const current = useWorkflowApp(open ? workflowId : undefined)
  const publish = usePublishApp(workflowId)
  const unpublish = useUnpublishApp(workflowId)

  const existing = current.data ?? null

  const initialSlug = useMemo(() => existing?.app_slug ?? '', [existing])
  const initialTitle = useMemo(() => existing?.title ?? workflowName, [existing, workflowName])
  const initialDescription = useMemo(() => existing?.description ?? '', [existing])

  const [title, setTitle] = useState(initialTitle)
  const [slug, setSlug] = useState(initialSlug)
  const [description, setDescription] = useState(initialDescription)
  const [copied, setCopied] = useState(false)

  const submit = () => {
    publish.mutate({
      title: title.trim() || undefined,
      app_slug: slug.trim() || undefined,
      description: description.trim() || undefined,
    })
  }

  const busy = publish.isPending || unpublish.isPending || current.isLoading
  const shareUrl = existing?.public_url ?? null

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

  return (
    <Modal
      open={open}
      onClose={busy ? () => {} : onClose}
      title="Publish as app"
      description="Share this workflow as a hosted chat page. The graph is snapshotted so live edits don't affect the running app until you re-publish."
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
      <div className="flex flex-col gap-4">
        {current.isLoading && (
          <div className="flex items-center gap-2 text-[12.5px] text-text-mute">
            <Loader2 size={12} className="animate-spin" />
            Loading current publish state…
          </div>
        )}
        {existing && shareUrl && (
          <div className="flex items-center gap-2 rounded-[10px] border border-border-faint bg-bg2 p-3">
            <Globe size={14} className="text-accent" />
            <div className="min-w-0 flex-1">
              <div className="text-[11px] uppercase tracking-wider text-text-faint">
                Live version {existing.version_num} · {existing.mode} · {existing.auth_mode}
              </div>
              <div className="truncate font-mono text-[12.5px] text-text">{shareUrl}</div>
            </div>
            <button
              onClick={copyLink}
              className="rounded-[6px] p-1.5 text-text-mute hover:bg-surface hover:text-text"
              title="Copy link"
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
            </button>
            <a
              href={shareUrl}
              target="_blank"
              rel="noreferrer"
              className="rounded-[6px] p-1.5 text-text-mute hover:bg-surface hover:text-text"
              title="Open"
            >
              <ExternalLink size={13} />
            </a>
          </div>
        )}

        <Field label="Title" hint="Shown as the page header + browser title.">
          <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Support Bot" />
        </Field>

        <Field label="Slug" hint="URL-safe identifier. Leave blank to auto-generate from the title.">
          <Input
            value={slug}
            onChange={e =>
              setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]+/g, '-'))
            }
            placeholder="support-bot"
          />
        </Field>

        <Field label="Description">
          <Textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={2}
            placeholder="Short line shown on the page + used for social share previews."
          />
        </Field>

        <p className="text-[11.5px] text-text-faint">
          Publishing snapshots the current graph as version{' '}
          {existing ? existing.version_num + 1 : 1}. Prior versions stay queryable so you can roll back
          later.
        </p>
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

import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2, PanelRightClose, PanelRightOpen } from 'lucide-react'
import axios from 'axios'
import { useAppConfig } from '../hooks/useAppConfig'
import { useAppSession, useAppendMessage } from '../hooks/useAppSession'
import { useSendMessage } from '../hooks/useSendMessage'
import { ThemeProvider } from '../theme/ThemeProvider'
import { AppHeader } from '../components/AppHeader'
import { MessageBubble } from '../components/MessageBubble'
import { WelcomeState } from '../components/WelcomeState'
import { InputBar } from '../components/InputBar'
import { CanvasView } from '../components/CanvasView'
import { PasswordGate } from '../components/PasswordGate'
import { FormView } from '../components/FormView'
import type { AttachedFile } from '../components/InputBar'
import type { AppMessage } from '../types/publicAppTypes'
import type { Artifact } from '../types/artifactTypes'

/**
 * Public chat page for /apps/:workspaceSlug/:appSlug.
 *
 * Two-pane layout: chat left, artifact canvas right. Canvas collapses when
 * empty (chat expands to full width) and pops open the moment any node
 * emits an artifact. Mobile drops the canvas into a slide-up sheet.
 */
export function PublicApp() {
  const params = useParams<{ workspaceSlug: string; appSlug: string }>()
  const ws = params.workspaceSlug ?? ''
  const slug = params.appSlug ?? ''

  const configQuery = useAppConfig(ws, slug)
  const sessionQuery = useAppSession(ws, slug, !!configQuery.data)
  const append = useAppendMessage(ws, slug)
  const [pending, setPending] = useState<AppMessage | null>(null)
  const [draft, setDraft] = useState('')
  const [attachments, setAttachments] = useState<AttachedFile[]>([])
  const [uploading, setUploading] = useState(false)

  const attach = async (file: File) => {
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const base = import.meta.env.VITE_API_URL || '/api/v1'
      const res = await axios.post(`${base}/apps/${ws}/${slug}/upload`, fd, {
        withCredentials: true,
      })
      setAttachments(prev => [...prev, res.data as AttachedFile])
    } catch {
      /* ignored; upload errors surfaced via banner in future */
    } finally {
      setUploading(false)
    }
  }
  const removeAttachment = (id: string) =>
    setAttachments(prev => prev.filter(a => a.id !== id))
  // Canvas starts hidden and unlocks the first time an artifact arrives.
  // We track a "user override" separately so once the visitor clicks the
  // toggle, we respect that choice from then on.
  const [canvasUserOpen, setCanvasUserOpen] = useState<boolean | null>(null)

  const { state: sendState, send, cancel } = useSendMessage(ws, slug, (finalMsg) => {
    append(finalMsg)
    setPending(null)
  })

  const optimistic = useMemo(() => {
    const messages = sessionQuery.data?.messages ?? []
    if (!pending) return messages
    return [...messages, pending]
  }, [sessionQuery.data?.messages, pending])

  // Every artifact across the transcript + the in-flight assistant message,
  // deduped by id so a rerender doesn't duplicate stream frames.
  const artifacts = useMemo<Artifact[]>(() => {
    const seen = new Set<string>()
    const out: Artifact[] = []
    for (const m of optimistic) {
      for (const a of (m.artifacts as Artifact[]) ?? []) {
        if (a?.id && !seen.has(a.id)) {
          seen.add(a.id)
          out.push(a)
        }
      }
    }
    for (const a of (sendState.assistant?.artifacts as Artifact[]) ?? []) {
      if (a?.id && !seen.has(a.id)) {
        seen.add(a.id)
        out.push(a)
      }
    }
    return out
  }, [optimistic, sendState.assistant?.artifacts])

  const canvasOpen = canvasUserOpen ?? artifacts.length > 0

  const scrollRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [optimistic, sendState.assistant?.content])

  const sendDraft = (text?: string) => {
    const value = (text ?? draft).trim()
    if (!value) return
    const userMsg: AppMessage = {
      id: `local-${Date.now()}`,
      session_id: sessionQuery.data?.session.id ?? '',
      role: 'user',
      content: value,
      artifacts: [],
      execution_id: null,
      tokens: 0,
      cost_usd: 0,
      latency_ms: 0,
      is_error: false,
      created_at: new Date().toISOString(),
    }
    setPending(userMsg)
    append(userMsg)
    setDraft('')
    void send(value)
  }

  if (configQuery.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0b0b0f] text-white/50">
        <Loader2 size={20} className="animate-spin" />
      </div>
    )
  }
  if (configQuery.isError || !configQuery.data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-2 bg-[#0b0b0f] px-6 text-center">
        <h1 className="text-[22px] font-semibold text-white">App not found</h1>
        <p className="max-w-sm text-[13px] text-white/50">
          Either the URL is wrong or this app was unpublished. Check the link with whoever shared it.
        </p>
      </div>
    )
  }

  const app = configQuery.data
  const isEmpty = optimistic.length === 0
  const canvasVisible = canvasOpen && artifacts.length > 0

  // Password gate: /session returns 401 with detail=password_required, or
  // for cross-origin dev may just be an error. Inspect the session
  // query's error before rendering chat.
  const sessionError = sessionQuery.error
  const needsPassword =
    app.auth_mode === 'password' &&
    (sessionQuery.data == null || (axios.isAxiosError(sessionError) && sessionError.response?.status === 401))
  if (needsPassword) {
    return (
      <ThemeProvider config={app.config}>
        <PasswordGate
          app={app}
          workspaceSlug={ws}
          appSlug={slug}
          onUnlocked={() => void sessionQuery.refetch()}
        />
      </ThemeProvider>
    )
  }

  // Form mode: no chat surface. One page in, one page out. Uses the
  // same send-message pipeline so streaming + artifacts still flow.
  if (app.mode === 'form') {
    return (
      <ThemeProvider config={app.config}>
        <div className="flex min-h-screen flex-col bg-[#0b0b0f] text-white">
          <AppHeader
            app={app}
            onNewChat={() => {
              sessionQuery.refetch()
              setPending(null)
            }}
          />
          <main className="flex min-h-0 flex-1 flex-col">
            {isEmpty ? (
              <FormView
                app={app}
                disabled={sendState.status === 'streaming' || sendState.status === 'sending'}
                onSubmit={(_values, summary) => sendDraft(summary || 'Submit')}
              />
            ) : (
              <div className="mx-auto flex w-full max-w-[860px] flex-1 flex-col gap-6 px-4 py-6 sm:px-6">
                {optimistic.map(m => (
                  <MessageBubble key={m.id} message={m} />
                ))}
                {sendState.assistant && (
                  <MessageBubble message={sendState.assistant} streaming />
                )}
                {canvasVisible && (
                  <div className="mt-4 min-h-[420px] overflow-hidden rounded-[12px] border border-white/5">
                    <CanvasView artifacts={artifacts} />
                  </div>
                )}
              </div>
            )}
          </main>
        </div>
      </ThemeProvider>
    )
  }

  return (
    <ThemeProvider config={app.config}>
      <div
        className="flex min-h-screen flex-col bg-[#0b0b0f] text-white"
        style={{
          background:
            app.config.background_data && app.config.background === 'gradient'
              ? String(app.config.background_data)
              : undefined,
        }}
      >
        <AppHeader
          app={app}
          onNewChat={() => {
            sessionQuery.refetch()
            setPending(null)
          }}
        />

        {/* Two-pane body: chat + canvas. Canvas hides on mobile below lg
            unless the user explicitly opens it, at which point it slides
            up as a bottom sheet. */}
        <div className="flex min-h-0 flex-1">
          <section className="flex min-w-0 flex-1 flex-col">
            <main className="mx-auto flex w-full max-w-[860px] flex-1 flex-col px-4 sm:px-6">
              <div ref={scrollRef} className="flex flex-1 flex-col gap-6 overflow-y-auto pb-24 pt-4">
                {isEmpty ? (
                  <WelcomeState app={app} onPickPrompt={p => sendDraft(p)} />
                ) : (
                  <>
                    {optimistic.map(m => (
                      <MessageBubble key={m.id} message={m} />
                    ))}
                    {sendState.assistant && (
                      <MessageBubble message={sendState.assistant} streaming />
                    )}
                  </>
                )}
              </div>
            </main>

            <div className="sticky bottom-0 z-20 border-t border-white/5 bg-[#0b0b0f]/85 px-4 py-3 backdrop-blur sm:px-6">
              <div className="mx-auto flex w-full max-w-[860px] items-end gap-2">
                <div className="flex-1">
                  <InputBar
                    value={draft}
                    onChange={setDraft}
                    onSubmit={() => sendDraft()}
                    onCancel={cancel}
                    disabled={sessionQuery.isLoading}
                    isStreaming={sendState.status === 'streaming' || sendState.status === 'sending'}
                    placeholder={`Message ${app.title}…`}
                    allowFileUpload={!!app.config.allow_file_upload}
                    attachments={attachments}
                    uploading={uploading}
                    onAttach={attach}
                    onRemoveAttachment={removeAttachment}
                  />
                </div>
                {artifacts.length > 0 && (
                  <button
                    onClick={() => setCanvasUserOpen(v => !(v ?? artifacts.length > 0))}
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-white/70 transition hover:bg-white/[0.08] hover:text-white lg:hidden"
                    title={canvasOpen ? 'Hide canvas' : 'Show canvas'}
                  >
                    {canvasOpen ? <PanelRightClose size={14} /> : <PanelRightOpen size={14} />}
                  </button>
                )}
              </div>
              {app.config.show_powered_by !== false && (
                <p className="mt-2 text-center text-[10.5px] text-white/30">
                  Powered by <span className="text-white/50">Fuse</span>
                </p>
              )}
            </div>
          </section>

          {/* Canvas — desktop side pane */}
          {canvasVisible && (
            <CanvasView
              artifacts={artifacts}
              className="hidden w-[42%] max-w-[560px] lg:flex"
            />
          )}
          {/* Canvas — mobile sheet */}
          {canvasVisible && (
            <div className="fixed inset-x-0 bottom-0 top-[64px] z-40 lg:hidden">
              <CanvasView
                artifacts={artifacts}
                onClose={() => setCanvasUserOpen(false)}

                className="h-full"
              />
            </div>
          )}
        </div>
      </div>
    </ThemeProvider>
  )
}

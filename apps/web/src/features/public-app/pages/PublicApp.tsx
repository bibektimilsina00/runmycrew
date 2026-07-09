import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAppConfig } from '../hooks/useAppConfig'
import { useAppSession, useAppendMessage } from '../hooks/useAppSession'
import { useSendMessage } from '../hooks/useSendMessage'
import { ThemeProvider } from '../theme/ThemeProvider'
import { AppHeader } from '../components/AppHeader'
import { MessageBubble } from '../components/MessageBubble'
import { WelcomeState } from '../components/WelcomeState'
import { InputBar } from '../components/InputBar'
import type { AppMessage } from '../types/publicAppTypes'

/**
 * Public chat page for /apps/:workspaceSlug/:appSlug.
 *
 * Renders with zero app chrome — no sidebar, no editor UI. The workflow's
 * output owns the frame.
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

  const { state: sendState, send, cancel } = useSendMessage(ws, slug, (finalMsg) => {
    append(finalMsg)
    setPending(null)
  })

  // Add the user turn locally so the transcript renders it immediately
  // (server already persisted it — we just need it in-view).
  const optimistic = useMemo(() => {
    const messages = sessionQuery.data?.messages ?? []
    if (!pending) return messages
    return [...messages, pending]
  }, [sessionQuery.data?.messages, pending])

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
            // Clears local view; the cookie session persists on server for history.
            sessionQuery.refetch()
            setPending(null)
          }}
        />

        <main className="mx-auto flex w-full max-w-[860px] flex-1 flex-col px-4 pb-6 pt-4 sm:px-6">
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
          <InputBar
            value={draft}
            onChange={setDraft}
            onSubmit={() => sendDraft()}
            onCancel={cancel}
            disabled={sessionQuery.isLoading}
            isStreaming={sendState.status === 'streaming' || sendState.status === 'sending'}
            placeholder={`Message ${app.title}…`}
          />
          {app.config.show_powered_by !== false && (
            <p className="mt-2 text-center text-[10.5px] text-white/30">
              Powered by <span className="text-white/50">Fuse</span>
            </p>
          )}
        </div>
      </div>
    </ThemeProvider>
  )
}

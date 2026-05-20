import React, { useEffect, useRef, useState, useCallback } from 'react'
import {
  ArrowUp,
  Settings,
  Square,
  Zap,
  CheckCircle,
  AlertCircle,
  Wand2,
  List,
  Type,
  RefreshCw,
  X,
  History,
  Trash2,
} from 'lucide-react'
import { useParams } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useCopilot, type CopilotMessage } from '@/features/workflow-editor/hooks/use-copilot'
import { useCopilotSettings } from '@/features/workflow-editor/hooks/use-copilot-settings'
import { useCopilotSessions, type CopilotSessionSummary } from '@/features/workflow-editor/hooks/use-copilot-sessions'
import { useUIStore } from '@/stores/ui-store'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api/client'
import { CustomSelect } from '@/features/workflow-editor/panels/inspector/components/custom-select'

// ── Provider selector ────────────────────────────────────────────────────────

function useProviders() {
  return useQuery({
    queryKey: ['copilot-providers'],
    queryFn: async () => {
      const res = await apiClient.get<{ providers: any[] }>('/copilot/providers')
      return res.data.providers
    },
    staleTime: 30_000,
  })
}

// ── Message bubble ────────────────────────────────────────────────────────────

function MessageBubble({ message }: { message: CopilotMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex flex-col gap-1', isUser && 'items-end')}>
      {isUser ? (
        <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-surface-5 px-3.5 py-2.5 text-[13px] text-white leading-relaxed">
          {message.content}
        </div>
      ) : (
        <div className="flex flex-col gap-2 w-full">
          {/* Streaming thinking indicator */}
          {message.isStreaming && !message.content && !message.toolCalls?.length && (
            <div className="flex items-center gap-1.5 text-text-muted text-[12px]">
              <span className="flex gap-0.5">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1 h-1 rounded-full bg-current animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </span>
              <span>Thinking…</span>
            </div>
          )}

          {/* Text content */}
          {message.content ? (
            <p className="text-[13px] text-white leading-relaxed whitespace-pre-wrap">
              {message.content}
              {message.isStreaming && (
                <span className="inline-block w-[3px] h-[13px] ml-0.5 bg-white/60 animate-pulse rounded-sm" />
              )}
            </p>
          ) : !message.isStreaming && !message.toolCalls?.length && (
            <p className="text-[13px] text-text-muted italic">No response</p>
          )}

          {/* Tool call indicators */}
          {message.toolCalls?.map((tc, i) => (
            <div
              key={i}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-2 border border-border text-[12px] text-text-muted"
            >
              {tc.tool === 'edit_workflow' ? (
                tc.success ? (
                  <CheckCircle className="size-3 text-green-500 shrink-0" />
                ) : (
                  <AlertCircle className="size-3 text-red-400 shrink-0" />
                )
              ) : (
                <Zap className="size-3 shrink-0" />
              )}
              <span>
                {tc.tool === 'edit_workflow'
                  ? tc.success
                    ? 'Workflow updated'
                    : 'Update failed'
                  : tc.tool === 'get_node_metadata'
                  ? 'Read node metadata'
                  : tc.tool}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Settings panel ───────────────────────────────────────────────────────────

function useModelOptions(provider: string, credentialId: string | null) {
  const [options, setOptions] = useState<{ label: string; value: string }[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const fetch = useCallback(async () => {
    if (!provider) return
    setIsLoading(true)
    try {
      const params: Record<string, string> = { provider }
      if (credentialId) params.credential = credentialId
      const res = await apiClient.get('/ai/models', { params })
      const raw: any[] = Array.isArray(res.data)
        ? res.data
        : res.data?.data ?? res.data?.options ?? res.data?.items ?? []
      setOptions(
        raw.map((o: any) => ({
          label: o.label ?? o.name ?? String(o.value ?? o),
          value: o.value ?? o.id ?? o,
        }))
      )
    } catch {
      setOptions([])
    } finally {
      setIsLoading(false)
    }
  }, [provider, credentialId])

  return { options, isLoading, refetch: fetch }
}

function SettingsPanel({
  settings,
  onUpdate,
  onClose,
}: {
  settings: ReturnType<typeof useCopilotSettings>['settings']
  onUpdate: (patch: Partial<typeof settings>) => void
  onClose: () => void
}) {
  const { data: providers = [] } = useProviders()
  const currentProvider = providers.find((p) => p.id === settings.provider)
  const { options: modelOptions, isLoading: modelsLoading, refetch: fetchModels } = useModelOptions(
    settings.provider,
    settings.credentialId
  )

  useEffect(() => {
    if (settings.modelMode === 'dynamic') fetchModels()
  }, [settings.modelMode, settings.provider, settings.credentialId])

  return (
    <div className="absolute inset-0 z-10 flex flex-col bg-[var(--bg)] border-b border-border">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-[13px] font-medium text-white">Model</span>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-text-muted hover:text-white hover:bg-surface-active transition-colors"
        >
          <X size={14} />
        </button>
      </div>
      <div className="flex flex-col gap-3 p-3 overflow-y-auto custom-scrollbar">

        {/* Provider — saves instantly */}
        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">Provider</label>
          <select
            value={settings.provider}
            onChange={(e) => onUpdate({ provider: e.target.value, credentialId: null, model: '' })}
            className="w-full bg-surface-2 border border-border rounded-md px-2.5 h-[34px] text-[13px] text-white focus:outline-none focus:border-border-strong"
          >
            {providers.length === 0 ? (
              <option value={settings.provider}>{settings.provider}</option>
            ) : (
              providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}{!p.hasCredential ? ' (no key)' : ''}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Credential — saves instantly */}
        {currentProvider?.credentials?.length > 0 && (
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">Credential</label>
            <select
              value={settings.credentialId || ''}
              onChange={(e) => onUpdate({ credentialId: e.target.value || null })}
              className="w-full bg-surface-2 border border-border rounded-md px-2.5 h-[34px] text-[13px] text-white focus:outline-none focus:border-border-strong"
            >
              <option value="">Auto-select</option>
              {currentProvider.credentials.map((c: any) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Model — toggle saves instantly, selection saves instantly */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between mb-0.5">
            <label className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">Model</label>
            <button
              onClick={() =>
                onUpdate({ modelMode: settings.modelMode === 'manual' ? 'dynamic' : 'manual' })
              }
              className="p-1 rounded hover:bg-surface-5 text-text-muted hover:text-white transition-all active:scale-95"
              title={settings.modelMode === 'manual' ? 'Switch to list' : 'Switch to manual input'}
            >
              {settings.modelMode === 'manual' ? <List size={12} /> : <Type size={12} />}
            </button>
          </div>

          {settings.modelMode === 'dynamic' ? (
            <div className="relative">
              <CustomSelect
                value={settings.model}
                options={modelOptions}
                onChange={(val) => onUpdate({ model: val })}
                placeholder={modelsLoading ? 'Loading models…' : 'Select a model'}
              />
              {modelsLoading && (
                <div className="absolute right-9 top-1/2 -translate-y-1/2">
                  <RefreshCw size={12} className="text-text-placeholder animate-spin" />
                </div>
              )}
            </div>
          ) : (
            <input
              type="text"
              value={settings.model}
              onChange={(e) => onUpdate({ model: e.target.value })}
              onBlur={(e) => onUpdate({ model: e.target.value })}
              placeholder={currentProvider?.defaultModel || 'e.g. claude-haiku-4-5-20251001'}
              className="w-full bg-surface-editor border border-border rounded-md px-3 h-[36px] text-[13px] text-white placeholder:text-text-placeholder focus:outline-none"
            />
          )}
        </div>

        {!currentProvider?.hasCredential && (
          <p className="text-[11px] text-amber-400 leading-snug">
            No credential for this provider. Add one in{' '}
            <span className="font-medium">Settings → Credentials</span>.
          </p>
        )}
      </div>
    </div>
  )
}

// ── History panel ─────────────────────────────────────────────────────────────

function HistoryPanel({
  sessions,
  currentSessionId,
  onSessionClick,
  onDeleteSession,
  onClose,
}: {
  sessions: CopilotSessionSummary[]
  currentSessionId: string | null
  onSessionClick: (session: CopilotSessionSummary) => void
  onDeleteSession: (sessionId: string) => void
  onClose: () => void
}) {
  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso)
      const now = new Date()
      const diffMs = now.getTime() - d.getTime()
      const diffDays = Math.floor(diffMs / 86_400_000)
      if (diffDays === 0) return 'Today'
      if (diffDays === 1) return 'Yesterday'
      if (diffDays < 7) return `${diffDays}d ago`
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    } catch {
      return ''
    }
  }

  return (
    <div className="absolute inset-0 z-10 flex flex-col bg-[var(--bg)]">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="text-[13px] font-medium text-white">History</span>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-text-muted hover:text-white hover:bg-surface-active transition-colors"
        >
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-12 px-4 text-center">
            <History className="size-8 text-text-muted opacity-40" />
            <p className="text-[12px] text-text-muted">No saved conversations yet</p>
          </div>
        ) : (
          <div className="flex flex-col py-1">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={cn(
                  'group flex items-center gap-2 px-3 py-2.5 cursor-pointer transition-colors',
                  'hover:bg-surface-2',
                  currentSessionId === session.id && 'bg-surface-2'
                )}
                onClick={() => onSessionClick(session)}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-white truncate leading-snug">{session.title}</p>
                  <p className="text-[11px] text-text-muted mt-0.5">{formatDate(session.updated_at)}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteSession(session.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded text-text-muted hover:text-red-400 hover:bg-surface-active transition-all shrink-0"
                  title="Delete session"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export const CopilotTab = React.memo(() => {
  const { id: workflowId = '' } = useParams<{ id: string }>()
  const [input, setInput] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const initialLoadDone = useRef(false)
  const { copilotView: view, setCopilotView: setView, copilotNewChatTrigger, copilotAutoPrompt, setCopilotAutoPrompt } = useUIStore()

  const { settings, updateSettings } = useCopilotSettings(workflowId)
  const { sessions, currentSessionId, isFetching, loadSession, deleteSession, startNewSession, onSessionSaved } =
    useCopilotSessions(workflowId)
  const { messages, setMessages, isLoading, error, sendMessage, stopStreaming } =
    useCopilot(workflowId, onSessionSaved)

  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // React to "New Chat" button in NodeHeader
  const newChatTriggerRef = useRef(copilotNewChatTrigger)
  useEffect(() => {
    if (copilotNewChatTrigger === newChatTriggerRef.current) return
    newChatTriggerRef.current = copilotNewChatTrigger
    handleNewChat()
  }, [copilotNewChatTrigger]) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-load most recent session once the fetch completes
  useEffect(() => {
    if (isFetching) return          // still loading — wait
    if (initialLoadDone.current) return
    initialLoadDone.current = true
    if (sessions.length > 0) {
      loadSession(sessions[0].id).then((msgs) => {
        if (msgs.length > 0) setMessages(msgs)
      })
    }
  }, [isFetching, sessions]) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-send template prompt once settings are ready
  const autoPromptFired = useRef(false)
  useEffect(() => {
    if (!copilotAutoPrompt || autoPromptFired.current || isFetching) return
    if (!settings.provider || !settings.credentialId) return
    autoPromptFired.current = true
    setCopilotAutoPrompt(null)
    sendMessage(
      copilotAutoPrompt,
      { provider: settings.provider, model: settings.model, credentialId: settings.credentialId },
      null
    )
  }, [copilotAutoPrompt, settings, isFetching]) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
  }

  const handleSend = () => {
    if (!input.trim() || isLoading) return
    sendMessage(
      input.trim(),
      { provider: settings.provider, model: settings.model, credentialId: settings.credentialId },
      currentSessionId
    )
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSessionClick = useCallback(
    async (session: CopilotSessionSummary) => {
      const msgs = await loadSession(session.id)
      if (msgs.length > 0) setMessages(msgs)
      setView('chat')
    },
    [loadSession, setMessages]
  )

  const handleNewChat = useCallback(() => {
    startNewSession()
    setMessages([])
    setView('chat')
  }, [startNewSession, setMessages])

  const handleDeleteSession = useCallback(
    async (sessionId: string) => {
      await deleteSession(sessionId)
      if (currentSessionId === sessionId) {
        setMessages([])
      }
    },
    [deleteSession, currentSessionId, setMessages]
  )

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative">
      {showSettings && (
        <SettingsPanel
          settings={settings}
          onUpdate={updateSettings}
          onClose={() => setShowSettings(false)}
        />
      )}

      {view === 'history' && (
        <HistoryPanel
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSessionClick={handleSessionClick}
          onDeleteSession={handleDeleteSession}
          onClose={() => setView('chat')}
        />
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-4 py-3 flex flex-col gap-4">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3 py-8 text-center">
            <div className="size-10 rounded-xl bg-surface-3 flex items-center justify-center">
              <Wand2 className="size-5 text-text-muted" />
            </div>
            <div>
              <p className="text-[13px] font-medium text-white">Fuse Copilot</p>
              <p className="text-[12px] text-text-muted mt-0.5 leading-snug">
                Describe the workflow you want to build
              </p>
            </div>
            <div className="flex flex-col gap-1.5 w-full max-w-[220px]">
              {[
                'Fetch data from an API and send to Slack',
                'Create a webhook that processes JSON and stores in Postgres',
                'Build an agent that answers questions',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="text-left text-[11px] text-text-muted hover:text-white px-2.5 py-1.5 rounded-md bg-surface-2 hover:bg-surface-3 border border-border transition-colors leading-snug"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Error banner */}
      {error && (
        <div className="mx-3 mb-2 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/30 text-[12px] text-red-400 leading-snug">
          {error}
        </div>
      )}

      {/* Input area */}
      <div className="p-3 pt-0 flex flex-col gap-1.5">
        <div className="rounded-2xl bg-surface-1 border border-border px-3 pt-2.5 pb-2 flex flex-col gap-2 focus-within:border-border-strong transition-all">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onInput={handleInput}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Describe what you want to build…"
            disabled={isLoading}
            className="w-full bg-transparent border-none text-[13px] text-white placeholder:text-text-placeholder resize-none focus:outline-none leading-relaxed disabled:opacity-50 min-h-[20px] max-h-[160px]"
          />
          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={cn(
                'p-1.5 rounded-md text-text-muted hover:text-white transition-colors',
                showSettings ? 'text-white bg-surface-active' : 'hover:bg-surface-active'
              )}
              title="Model settings"
            >
              <Settings className="size-3.5" />
            </button>
            <button
              onClick={isLoading ? stopStreaming : handleSend}
              disabled={!isLoading && !input.trim()}
              className={cn(
                'flex items-center justify-center size-7 rounded-full transition-all',
                isLoading
                  ? 'bg-white/10 hover:bg-white/20 text-white'
                  : input.trim()
                  ? 'bg-white text-black hover:bg-white/90 active:scale-95'
                  : 'bg-surface-5 text-text-muted cursor-not-allowed'
              )}
            >
              {isLoading ? <Square className="size-3" /> : <ArrowUp className="size-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
})

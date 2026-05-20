import { useState, useCallback, useRef } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import { useWorkflowStore } from '@/stores/workflow-store'

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

export type CopilotMessageRole = 'user' | 'assistant'

export interface CopilotMessage {
  id: string
  role: CopilotMessageRole
  content: string
  toolCalls?: { tool: string; success: boolean }[]
  workflowUpdated?: boolean
  isStreaming?: boolean
}

export interface CopilotSettings {
  provider: string
  model: string
  credentialId: string | null
}

interface SSEEvent {
  type: string
  content?: string
  tool?: string
  success?: boolean
  errors?: string[]
  graph?: { nodes: any[]; edges: any[] }
  message?: string
  session_id?: string
  title?: string
}

export function useCopilot(
  workflowId: string,
  onSessionSaved?: (id: string, title: string) => void
) {
  const token = useAuthStore((s) => s.token)
  const { setNodes, setEdges } = useWorkflowStore()

  const [messages, setMessages] = useState<CopilotMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (content: string, settings: CopilotSettings, sessionId: string | null = null) => {
      if (!content.trim() || isLoading) return

      // Abort any in-progress stream
      abortRef.current?.abort()
      abortRef.current = new AbortController()

      const userMsg: CopilotMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
      }

      // Build conversation history to send (role + content only)
      const history = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content,
      }))

      setMessages((prev) => [...prev, userMsg])
      setError(null)
      setIsLoading(true)

      // Create streaming assistant message placeholder
      const assistantId = crypto.randomUUID()
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: 'assistant',
          content: '',
          isStreaming: true,
          toolCalls: [],
        },
      ])

      try {
        const resp = await fetch(`${API_BASE}/copilot/${workflowId}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            messages: history,
            graph: {
              nodes: useWorkflowStore.getState().nodes,
              edges: useWorkflowStore.getState().edges,
            },
            provider: settings.provider,
            model: settings.model || undefined,
            credential_id: settings.credentialId || undefined,
            session_id: sessionId || undefined,
          }),
          signal: abortRef.current.signal,
        })

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({ detail: resp.statusText }))
          throw new Error(err.detail || `HTTP ${resp.status}`)
        }

        const reader = resp.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let accumulated = ''
        let toolCalls: { tool: string; success: boolean }[] = []
        let workflowUpdated = false

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const raw = line.slice(6).trim()
            if (!raw) continue

            let evt: SSEEvent
            try {
              evt = JSON.parse(raw)
            } catch {
              continue
            }

            if (evt.type === 'text_delta' && evt.content) {
              accumulated += evt.content
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: accumulated } : m
                )
              )
            } else if (evt.type === 'tool_result' && evt.tool) {
              toolCalls = [
                ...toolCalls,
                { tool: evt.tool, success: evt.success ?? true },
              ]
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, toolCalls } : m
                )
              )
            } else if (evt.type === 'workflow_updated' && evt.graph) {
              workflowUpdated = true
              setNodes(evt.graph.nodes)
              setEdges(evt.graph.edges)
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, workflowUpdated: true } : m
                )
              )
            } else if (evt.type === 'session_saved' && evt.session_id) {
              onSessionSaved?.(evt.session_id, evt.title ?? 'New Chat')
            } else if (evt.type === 'error') {
              throw new Error(evt.message || 'Copilot error')
            } else if (evt.type === 'done') {
              break
            }
          }
        }

        // Finalize assistant message
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: accumulated || (workflowUpdated ? 'Workflow updated.' : ''),
                  isStreaming: false,
                  toolCalls,
                  workflowUpdated,
                }
              : m
          )
        )
      } catch (err: any) {
        if (err.name === 'AbortError') {
          // User cancelled — remove the empty streaming message
          setMessages((prev) => prev.filter((m) => m.id !== assistantId))
        } else {
          const msg = err.message || 'Something went wrong'
          setError(msg)
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: `Error: ${msg}`, isStreaming: false }
                : m
            )
          )
        }
      } finally {
        setIsLoading(false)
      }
    },
    [workflowId, token, messages, isLoading, setNodes, setEdges, onSessionSaved]
  )

  const clearMessages = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setError(null)
  }, [])

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    setIsLoading(false)
  }, [])

  return { messages, setMessages, isLoading, error, sendMessage, clearMessages, stopStreaming }
}

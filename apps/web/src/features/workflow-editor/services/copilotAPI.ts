import apiClient from '@/shared/utils/apiClient'
import { useAuthStore } from '@/features/auth/store/authStore'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'

const BASE = import.meta.env.VITE_API_URL || '/api/v1'

export interface CopilotEvent {
  type:
    | 'text_delta'
    | 'tool_start'
    | 'tool_result'
    | 'graph_op'
    | 'workflow_proposed'
    | 'session_saved'
    | 'error'
    | 'done'
  [key: string]: unknown
}

export interface ChatRequestBody {
  messages: { role: string; content: string }[]
  graph?: { nodes: unknown[]; edges: unknown[] }
  provider?: string
  model?: string | null
  credential_id?: string | null
  session_id?: string | null
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  let token = useAuthStore.getState().token
  if (!token) {
    try {
      token = localStorage.getItem('runmycrew-auth-token')
    } catch {
      token = null
    }
  }
  if (token) headers.Authorization = `Bearer ${token}`
  const workspaceId = useWorkspaceStore.getState().currentWorkspaceId
  if (workspaceId) headers['X-Workspace-ID'] = workspaceId
  return headers
}

/**
 * POST the chat request and yield parsed SSE events. Uses fetch + ReadableStream
 * (axios can't stream in the browser). Abort via the provided signal.
 */
export async function* streamCopilotChat(
  workflowId: string,
  body: ChatRequestBody,
  signal: AbortSignal,
): AsyncGenerator<CopilotEvent> {
  const resp = await fetch(`${BASE}/copilot/${workflowId}/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(body),
    signal,
  })

  if (!resp.ok || !resp.body) {
    let detail = `Request failed (HTTP ${resp.status})`
    try {
      const data = await resp.json()
      if (data?.detail) detail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    } catch {
      // non-JSON error body — keep default
    }
    throw new Error(detail)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let sep: number
    while ((sep = buffer.indexOf('\n\n')) !== -1) {
      const rawEvent = buffer.slice(0, sep)
      buffer = buffer.slice(sep + 2)
      const dataLine = rawEvent.split('\n').find(l => l.startsWith('data:'))
      if (!dataLine) continue
      const data = dataLine.slice(5).trim()
      if (!data) continue
      try {
        yield JSON.parse(data) as CopilotEvent
      } catch {
        // ignore malformed chunk
      }
    }
  }
}

// ── REST: chat sessions ───────────────────────────────────────────────────────

export interface SessionItem {
  id: string
  title: string
  created_at: string | null
  updated_at: string | null
}

export const copilotAPI = {
  listSessions: (workflowId: string) =>
    apiClient
      .get<{ sessions: SessionItem[] }>(`/copilot/${workflowId}/sessions`)
      .then(r => r.data.sessions),
  getSession: (workflowId: string, sessionId: string) =>
    apiClient
      .get<{ id: string; title: string; messages: { role: string; content: string }[] }>(
        `/copilot/${workflowId}/sessions/${sessionId}`,
      )
      .then(r => r.data),
  deleteSession: (workflowId: string, sessionId: string) =>
    apiClient.delete(`/copilot/${workflowId}/sessions/${sessionId}`),
}

import { useState, useEffect, useCallback } from 'react'
import apiClient from '@/lib/api/client'
import type { CopilotMessage } from './use-copilot'

export interface CopilotSessionSummary {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface CopilotSessionDetail extends CopilotSessionSummary {
  messages: CopilotMessage[]
}

export function useCopilotSessions(workflowId: string) {
  const [sessions, setSessions] = useState<CopilotSessionSummary[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isFetching, setIsFetching] = useState(true) // true until first fetch completes

  const fetchSessions = useCallback(async () => {
    if (!workflowId) return
    setIsFetching(true)
    try {
      const res = await apiClient.get(`/copilot/${workflowId}/sessions`)
      setSessions(res.data.sessions || [])
    } catch {
      // ignore — network errors shouldn't break the UI
    } finally {
      setIsFetching(false)
    }
  }, [workflowId])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  const loadSession = useCallback(
    async (sessionId: string): Promise<CopilotMessage[]> => {
      setIsLoading(true)
      try {
        const res = await apiClient.get(`/copilot/${workflowId}/sessions/${sessionId}`)
        setCurrentSessionId(sessionId)
        return (res.data.messages || []).map((m: any) => ({
          id: crypto.randomUUID(),
          role: m.role as 'user' | 'assistant',
          content: m.content,
          toolCalls: m.tool_calls,
          workflowUpdated: m.workflow_updated,
        }))
      } catch {
        return []
      } finally {
        setIsLoading(false)
      }
    },
    [workflowId]
  )

  const deleteSession = useCallback(
    async (sessionId: string) => {
      await apiClient.delete(`/copilot/${workflowId}/sessions/${sessionId}`)
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (currentSessionId === sessionId) setCurrentSessionId(null)
    },
    [workflowId, currentSessionId]
  )

  const startNewSession = useCallback(() => {
    setCurrentSessionId(null)
  }, [])

  const onSessionSaved = useCallback((sessionId: string, title: string) => {
    setCurrentSessionId(sessionId)
    setSessions((prev) => {
      const exists = prev.find((s) => s.id === sessionId)
      if (exists) {
        return prev.map((s) =>
          s.id === sessionId ? { ...s, title, updated_at: new Date().toISOString() } : s
        )
      }
      return [
        {
          id: sessionId,
          title,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        ...prev,
      ]
    })
  }, [])

  return {
    sessions,
    currentSessionId,
    isLoading,
    isFetching,
    fetchSessions,
    loadSession,
    deleteSession,
    startNewSession,
    onSessionSaved,
  }
}

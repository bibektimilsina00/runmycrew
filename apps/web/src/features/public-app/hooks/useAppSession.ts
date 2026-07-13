import { useQuery, useQueryClient } from '@tanstack/react-query'
import { publicAppAPI } from '../services/publicAppAPI'
import type { AppMessage } from '../types/publicAppTypes'

/**
 * Boots the visitor's session (get-or-create) and returns the session +
 * hydrated prior messages. Called once on mount by PublicApp.
 */
export function useAppSession(workspaceSlug: string, appSlug: string, enabled = true) {
  return useQuery({
    queryKey: ['public-app-session', workspaceSlug, appSlug],
    queryFn: () => publicAppAPI.ensureSession(workspaceSlug, appSlug),
    enabled,
    retry: 1,
    staleTime: 0,
  })
}

/** All of the visitor's conversations for the sidebar. */
export function useSessionList(workspaceSlug: string, appSlug: string, enabled = true) {
  return useQuery({
    queryKey: ['public-app-sessions', workspaceSlug, appSlug],
    queryFn: () => publicAppAPI.listSessions(workspaceSlug, appSlug),
    enabled,
    retry: 1,
    staleTime: 10_000,
  })
}

/** One conversation's transcript, keyed by session id. */
export function useConversation(
  workspaceSlug: string,
  appSlug: string,
  sessionId: string | null,
) {
  return useQuery({
    queryKey: ['public-app-conversation', workspaceSlug, appSlug, sessionId],
    queryFn: () => publicAppAPI.getSession(workspaceSlug, appSlug, sessionId!),
    enabled: !!sessionId,
    retry: 1,
    staleTime: 0,
  })
}

export function useAppendMessage(
  workspaceSlug: string,
  appSlug: string,
  sessionId: string | null,
) {
  const qc = useQueryClient()
  return (msg: AppMessage) => {
    if (!sessionId) return
    const key = ['public-app-conversation', workspaceSlug, appSlug, sessionId]
    void (async () => {
      // Cancel any in-flight conversation fetch FIRST: its snapshot was
      // taken before this message existed server-side, and letting it
      // land after the append silently erased the visitor's entry.
      await qc.cancelQueries({ queryKey: key })
      qc.setQueryData(key, (prev: unknown) => {
        const envelope = prev as { session: unknown; messages: AppMessage[] } | undefined
        // Nothing hydrated yet (fast submit): seed a minimal envelope
        // instead of dropping the message.
        if (!envelope) return { session: null, messages: [msg] }
        return { ...envelope, messages: [...envelope.messages, msg] }
      })
    })()
    // Keep the sidebar ordering/preview fresh after the turn.
    void qc.invalidateQueries({ queryKey: ['public-app-sessions', workspaceSlug, appSlug] })
  }
}

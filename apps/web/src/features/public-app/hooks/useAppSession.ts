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
    qc.setQueryData(
      ['public-app-conversation', workspaceSlug, appSlug, sessionId],
      (prev: unknown) => {
        const envelope = prev as { session: unknown; messages: AppMessage[] } | undefined
        if (!envelope) return prev
        return { ...envelope, messages: [...envelope.messages, msg] }
      },
    )
    // Keep the sidebar ordering/preview fresh after the turn.
    void qc.invalidateQueries({ queryKey: ['public-app-sessions', workspaceSlug, appSlug] })
  }
}

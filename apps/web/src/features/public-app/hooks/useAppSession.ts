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

export function useAppendMessage(workspaceSlug: string, appSlug: string) {
  const qc = useQueryClient()
  return (msg: AppMessage) => {
    qc.setQueryData(['public-app-session', workspaceSlug, appSlug], (prev: unknown) => {
      const envelope = prev as { session: unknown; messages: AppMessage[] } | undefined
      if (!envelope) return prev
      return { ...envelope, messages: [...envelope.messages, msg] }
    })
  }
}

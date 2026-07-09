import { useQuery } from '@tanstack/react-query'
import { publicAppAPI } from '../services/publicAppAPI'

/**
 * Loads the public app config for the given workspace + app slug pair.
 * Retries are disabled because a 404 = "app not found" and should surface
 * immediately, not spin.
 */
export function useAppConfig(workspaceSlug: string, appSlug: string) {
  return useQuery({
    queryKey: ['public-app', workspaceSlug, appSlug],
    queryFn: ({ signal }) => publicAppAPI.getConfig(workspaceSlug, appSlug, signal),
    retry: false,
    staleTime: 1000 * 60 * 5,
  })
}

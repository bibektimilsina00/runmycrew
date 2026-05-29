import { useQuery } from '@tanstack/react-query'
import { logsAPI } from '@/features/logs/services/logsAPI'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'

export function useLogs(level?: string) {
  const workspaceId = useWorkspaceStore((state) => state.currentWorkspaceId)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['logs', workspaceId, level ?? 'all'],
    queryFn: ({ signal }) => logsAPI.getAll({ level }, signal),
    enabled: !!workspaceId,
    staleTime: 1000 * 30,
  })

  return { items: data ?? [], isLoading, refetch }
}

import { useQuery } from '@tanstack/react-query'
import { runsAPI } from '@/features/runs/services/runsAPI'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'

export function useRunsCount() {
  const workspaceId = useWorkspaceStore((state) => state.currentWorkspaceId)
  return useQuery({
    queryKey: ['runs', 'count', workspaceId],
    queryFn: ({ signal }) => runsAPI.getAll(signal).then((res) => res.total),
    enabled: !!workspaceId,
    staleTime: 1000 * 30,
  })
}

import { useQuery } from '@tanstack/react-query'
import { dashboardAPI } from '../services/dashboardAPI'

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn:  ({ signal }) => dashboardAPI.getStats(signal),
    staleTime: 1000 * 30,
    refetchInterval: 60_000,
  })
}

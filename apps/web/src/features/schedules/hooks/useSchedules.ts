import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { schedulesAPI } from '../services/schedulesAPI'
// Reuse workflow actions from automations
import { automationsAPI } from '@/features/automations/services/automationsAPI'

const KEYS = { list: ['schedules'] as const }

export function useSchedules() {
  return useQuery({
    queryKey: KEYS.list,
    queryFn: ({ signal }) => schedulesAPI.listAll(signal),
    staleTime: 1000 * 30,
    refetchInterval: 60_000, // refresh every minute so next_run stays accurate
  })
}

export function useToggleSchedule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => automationsAPI.toggle(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useDeleteSchedule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => automationsAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useRunSchedule() {
  return useMutation({
    mutationFn: (id: string) => automationsAPI.run(id),
  })
}

export function useValidateCron() {
  return useMutation({
    mutationFn: (expression: string) => schedulesAPI.validateCron(expression),
  })
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { automationsAPI } from '../services/automationsAPI'
import type { WorkflowCreateRequest } from '../types/automationsTypes'

const KEYS = { list: ['automations'] as const }

export function useAutomations() {
  return useQuery({
    queryKey: KEYS.list,
    queryFn: ({ signal }) => automationsAPI.list(signal),
    staleTime: 1000 * 30,
  })
}

export function useCreateAutomation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: WorkflowCreateRequest) => automationsAPI.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useDeleteAutomation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => automationsAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useToggleAutomation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => automationsAPI.toggle(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useDuplicateAutomation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => automationsAPI.duplicate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useRunAutomation() {
  return useMutation({
    mutationFn: (id: string) => automationsAPI.run(id),
  })
}

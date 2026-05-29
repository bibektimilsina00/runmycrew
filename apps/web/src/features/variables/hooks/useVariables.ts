import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { variablesAPI } from '../services/variablesAPI'
import type { VariableCreateRequest, VariableUpdateRequest } from '../types/variablesTypes'

const KEYS = {
  all: ['variables'] as const,
  list: () => [...KEYS.all, 'list'] as const,
}

export function useVariables() {
  return useQuery({
    queryKey: KEYS.list(),
    queryFn: ({ signal }) => variablesAPI.list(signal),
    staleTime: 1000 * 30,
  })
}

export function useCreateVariable() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: VariableCreateRequest) => variablesAPI.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list() }),
  })
}

export function useUpdateVariable() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: VariableUpdateRequest }) =>
      variablesAPI.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list() }),
  })
}

export function useDeleteVariable() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => variablesAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list() }),
  })
}

export function useRevealVariable() {
  return useMutation({
    mutationFn: (id: string) => variablesAPI.reveal(id),
  })
}

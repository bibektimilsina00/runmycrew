import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { loopsAPI } from '../services/loopsAPI'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { LoopCreateRequest } from '../types/loopsTypes'

const KEYS = { list: ['loops'] as const }

export function useLoops() {
  return useQuery({
    queryKey: KEYS.list,
    queryFn: ({ signal }) => loopsAPI.list(signal),
    staleTime: 1000 * 30,
  })
}

/**
 * Create a loop workflow (kind:'loop') and navigate straight into the shared
 * editor at /workflows/:id. Because the loaded workflow's kind === 'loop', the
 * editor renders the focused Loop Engineering palette.
 */
export function useCreateLoop() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: (data: LoopCreateRequest) => loopsAPI.create(data),
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: KEYS.list })
      navigate(APP_ROUTES.WORKFLOW(created.id))
    },
  })
}

export function useDeleteLoop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => loopsAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useToggleLoop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => loopsAPI.toggle(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useDuplicateLoop() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => loopsAPI.duplicate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useRunLoop() {
  return useMutation({
    mutationFn: (id: string) => loopsAPI.run(id),
  })
}

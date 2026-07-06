import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { loopsAPI } from '../services/loopsAPI'
import { editorAPI } from '@/features/workflow-editor/services/editorAPI'
import { APP_ROUTES } from '@/shared/constants/routes'
import { buildStarterCrew } from '../utils/starterCrew'
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
 * Create a crew and navigate straight into the shared editor at /crews/:id.
 * The /crews route loads the editor in `entity="crew"` mode, which forces the
 * focused Crew palette (no `kind` needed).
 */
export function useCreateLoop() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: async (data: LoopCreateRequest) => {
      // Seed a starter crew so the loop opens with the canvas already populated.
      // Reuse the shared node-definitions cache (same key the editor uses) to
      // resolve which node types exist, then build the graph defensively —
      // missing node types simply drop out. A caller-supplied graph wins.
      let graph = data.graph
      if (!graph) {
        try {
          const defs = await qc.ensureQueryData({
            queryKey: ['node-definitions'],
            queryFn: ({ signal }) => editorAPI.getNodeDefinitions(signal),
            staleTime: 1000 * 60 * 10,
          })
          const types = new Set(defs.map(d => d.type))
          const starter = buildStarterCrew(types)
          if (starter.nodes.length > 0) graph = starter
        } catch {
          // Non-fatal: fall back to an empty loop if definitions can't load.
        }
      }
      return loopsAPI.create({ ...data, graph })
    },
    onSuccess: (created) => {
      qc.invalidateQueries({ queryKey: KEYS.list })
      navigate(APP_ROUTES.CREW_EDITOR(created.id))
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

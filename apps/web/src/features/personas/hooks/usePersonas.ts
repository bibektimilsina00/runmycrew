import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { personasAPI } from '../services/personasAPI'
import type { PersonaCreateRequest, PersonaUpdateRequest } from '../types/personaTypes'

const KEYS = {
  list: ['personas'] as const,
  detail: (id: string) => ['personas', id] as const,
}

export function usePersonas() {
  return useQuery({
    queryKey: KEYS.list,
    queryFn: ({ signal }) => personasAPI.list(signal),
    staleTime: 1000 * 30,
  })
}

export function usePersona(id: string | undefined) {
  return useQuery({
    queryKey: id ? KEYS.detail(id) : ['personas', 'noop'],
    queryFn: () => personasAPI.get(id as string),
    enabled: !!id,
  })
}

export function useCreatePersona() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PersonaCreateRequest) => personasAPI.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useUpdatePersona(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PersonaUpdateRequest) => personasAPI.update(id, data),
    onSuccess: (persona) => {
      qc.invalidateQueries({ queryKey: KEYS.list })
      qc.setQueryData(KEYS.detail(id), persona)
    },
  })
}

export function useDeletePersona() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => personasAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function usePublicPersonas() {
  return useQuery({
    queryKey: ['personas', 'public'],
    queryFn: ({ signal }) => personasAPI.listPublic(signal),
    staleTime: 1000 * 60,
  })
}

export function useImportPersona() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sourceId: string) => personasAPI.import(sourceId),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

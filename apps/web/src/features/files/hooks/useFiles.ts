import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { filesAPI } from '../services/filesAPI'

export const fileKeys = {
  all: ['files'] as const,
  list: () => [...fileKeys.all, 'list'] as const,
  stats: () => [...fileKeys.all, 'stats'] as const,
}

export function useFiles() {
  return useQuery({
    queryKey: fileKeys.list(),
    queryFn: ({ signal }) => filesAPI.list(signal),
    staleTime: 1000 * 30,
  })
}

export function useFileStats() {
  return useQuery({
    queryKey: fileKeys.stats(),
    queryFn: ({ signal }) => filesAPI.stats(signal),
    staleTime: 1000 * 30,
  })
}

export function useUploadFile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => filesAPI.upload(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: fileKeys.list() })
      qc.invalidateQueries({ queryKey: fileKeys.stats() })
    },
  })
}

export function useRenameFile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => filesAPI.rename(id, name),
    onSuccess: () => qc.invalidateQueries({ queryKey: fileKeys.list() }),
  })
}

export function useDeleteFile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => filesAPI.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: fileKeys.list() })
      qc.invalidateQueries({ queryKey: fileKeys.stats() })
    },
  })
}

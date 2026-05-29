import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { knowledgeAPI } from '../services/knowledgeAPI'
import type { KBCreateRequest } from '../types/knowledgeTypes'

const KEYS = {
  list: ['kb', 'list'] as const,
  detail: (id: string) => ['kb', id] as const,
}

export function useKBList() {
  return useQuery({
    queryKey: KEYS.list,
    queryFn: ({ signal }) => knowledgeAPI.list(signal),
    staleTime: 1000 * 30,
  })
}

export function useKBDetail(id: string | null) {
  return useQuery({
    queryKey: KEYS.detail(id ?? ''),
    queryFn: ({ signal }) => knowledgeAPI.get(id!, signal),
    enabled: !!id,
    staleTime: 1000 * 30,
  })
}

export function useCreateKB() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: KBCreateRequest) => knowledgeAPI.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useDeleteKB() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => knowledgeAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.list }),
  })
}

export function useAddTextDoc(kbId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ name, text }: { name: string; text: string }) =>
      knowledgeAPI.addTextDoc(kbId, name, text),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.detail(kbId) })
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useUploadDoc(kbId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => knowledgeAPI.uploadDoc(kbId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.detail(kbId) })
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useAddUrlDoc(kbId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (url: string) => knowledgeAPI.addUrlDoc(kbId, url),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.detail(kbId) })
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useDeleteDoc(kbId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (docId: string) => knowledgeAPI.deleteDoc(kbId, docId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.detail(kbId) })
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useChunks(kbId: string, docId: string) {
  return useQuery({
    queryKey: ['kb', kbId, 'doc', docId, 'chunks'],
    queryFn: ({ signal }) => knowledgeAPI.listChunks(kbId, docId, signal),
    enabled: !!kbId && !!docId,
    staleTime: 1000 * 30,
  })
}

export function useCreateChunk(kbId: string, docId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (content: string) => knowledgeAPI.createChunk(kbId, docId, content),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb', kbId, 'doc', docId, 'chunks'] })
      qc.invalidateQueries({ queryKey: KEYS.detail(kbId) })
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useUpdateChunk(kbId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ chunkId, content }: { chunkId: string; content: string }) =>
      knowledgeAPI.updateChunk(kbId, chunkId, content),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['kb', kbId] }),
  })
}

export function useDeleteChunk(kbId: string, docId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (chunkId: string) => knowledgeAPI.deleteChunk(kbId, chunkId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['kb', kbId, 'doc', docId, 'chunks'] })
      qc.invalidateQueries({ queryKey: KEYS.detail(kbId) })
    },
  })
}

export function useReindexDoc(kbId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (docId: string) => knowledgeAPI.reindexDoc(kbId, docId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.detail(kbId) })
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useReindex(kbId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => knowledgeAPI.reindex(kbId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.detail(kbId) })
      qc.invalidateQueries({ queryKey: KEYS.list })
    },
  })
}

export function useKBSearch(kbId: string) {
  return useMutation({
    mutationFn: ({ query, top_k }: { query: string; top_k?: number }) =>
      knowledgeAPI.search(kbId, query, top_k),
  })
}

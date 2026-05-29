import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { connectionsAPI } from '../services/connectionsAPI'

const KEYS = {
  credentials: ['connections', 'credentials'] as const,
  providers:   ['connections', 'providers']   as const,
  audit:       ['connections', 'audit']        as const,
}

export function useCredentials() {
  return useQuery({
    queryKey: KEYS.credentials,
    queryFn: ({ signal }) => connectionsAPI.listCredentials(signal),
    staleTime: 1000 * 30,
  })
}

export function useProviders() {
  return useQuery({
    queryKey: KEYS.providers,
    queryFn: ({ signal }) => connectionsAPI.listProviders(signal),
    staleTime: 1000 * 60 * 5,
  })
}

export function useCreateCredential() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; type: string; data: Record<string, string> }) =>
      connectionsAPI.createCredential(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.credentials }),
  })
}

export function useRenameCredential() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      connectionsAPI.renameCredential(id, name),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.credentials }),
  })
}

export function useDeleteCredential() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => connectionsAPI.deleteCredential(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.credentials }),
  })
}

export function useAuditLog(enabled: boolean) {
  return useQuery({
    queryKey: KEYS.audit,
    queryFn: ({ signal }) => connectionsAPI.listAuditLog(signal),
    enabled,
    staleTime: 1000 * 30,
  })
}

export function useOAuthUrl() {
  return useMutation({
    mutationFn: ({ service, name }: { service: string; name?: string }) =>
      connectionsAPI.getOAuthUrl(service, name),
  })
}

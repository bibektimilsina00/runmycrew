import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { appsOwnerAPI } from '../services/appsOwnerAPI'
import type { PublishAppRequest } from '../types/appsOwnerTypes'

const KEYS = {
  current: (workflowId: string) => ['workflow-app', workflowId] as const,
  versions: (workflowId: string) => ['workflow-app', workflowId, 'versions'] as const,
}

export function useWorkflowApp(workflowId: string | undefined) {
  return useQuery({
    queryKey: workflowId ? KEYS.current(workflowId) : ['workflow-app', 'noop'],
    queryFn: () => appsOwnerAPI.current(workflowId as string),
    enabled: !!workflowId,
  })
}

export function useWorkflowAppVersions(workflowId: string | undefined) {
  return useQuery({
    queryKey: workflowId ? KEYS.versions(workflowId) : ['workflow-app', 'noop', 'versions'],
    queryFn: () => appsOwnerAPI.versions(workflowId as string),
    enabled: !!workflowId,
  })
}

export function usePublishApp(workflowId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PublishAppRequest) => appsOwnerAPI.publish(workflowId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.current(workflowId) })
      qc.invalidateQueries({ queryKey: KEYS.versions(workflowId) })
    },
  })
}

export function useUnpublishApp(workflowId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => appsOwnerAPI.unpublish(workflowId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.current(workflowId) })
    },
  })
}

export function useRollbackApp(workflowId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: { version_num: number }) => appsOwnerAPI.rollback(workflowId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.current(workflowId) })
      qc.invalidateQueries({ queryKey: KEYS.versions(workflowId) })
    },
  })
}

export function useResetApiKey(workflowId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => appsOwnerAPI.resetApiKey(workflowId),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.current(workflowId) }),
  })
}

export function useAnalytics(workflowId: string | undefined) {
  return useQuery({
    queryKey: workflowId ? ['workflow-app', workflowId, 'analytics'] : ['workflow-app', 'noop', 'analytics'],
    queryFn: () => appsOwnerAPI.analytics(workflowId as string),
    enabled: !!workflowId,
    staleTime: 1000 * 30,
  })
}

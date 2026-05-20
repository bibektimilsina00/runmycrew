export const workflowKeys = {
  all: ['workflows'] as const,
  lists: (workspaceId?: string | null) => [...workflowKeys.all, workspaceId ?? 'no-workspace', 'list'] as const,
  list: (workspaceId?: string | null, filters?: Record<string, unknown>) => [...workflowKeys.lists(workspaceId), filters] as const,
  details: () => [...workflowKeys.all, 'detail'] as const,
  detail: (id: string, workspaceId?: string | null) => [...workflowKeys.details(), workspaceId ?? 'no-workspace', id] as const,
}

export const folderKeys = {
  all: ['folders'] as const,
  lists: (workspaceId?: string | null) => [...folderKeys.all, workspaceId ?? 'no-workspace', 'list'] as const,
  list: (workspaceId?: string | null, filters?: Record<string, unknown>) => [...folderKeys.lists(workspaceId), filters] as const,
  details: () => [...folderKeys.all, 'detail'] as const,
  detail: (id: string, workspaceId?: string | null) => [...folderKeys.details(), workspaceId ?? 'no-workspace', id] as const,
}

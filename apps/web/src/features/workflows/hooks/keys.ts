export const workflowKeys = {
  all: ['workflows'] as const,
  lists: (workspaceId: string | null) => [...workflowKeys.all, workspaceId, 'list'] as const,
  detail: (id: string, workspaceId: string | null) => [...workflowKeys.all, workspaceId, 'detail', id] as const,
}

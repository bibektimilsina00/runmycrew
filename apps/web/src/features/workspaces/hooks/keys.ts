export const workspaceKeys = {
  all: ['workspaces'] as const,
  lists: () => [...workspaceKeys.all, 'list'] as const,
  members: (workspaceId: string | null) => [...workspaceKeys.all, workspaceId, 'members'] as const,
  invite: (token: string | undefined) => [...workspaceKeys.all, 'invite', token] as const,
}

export const folderKeys = {
  all: ['folders'] as const,
  lists: (workspaceId: string | null) => [...folderKeys.all, workspaceId, 'list'] as const,
}

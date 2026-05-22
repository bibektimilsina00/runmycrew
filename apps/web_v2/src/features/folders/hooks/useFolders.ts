import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { folderAPI } from '../services/folderAPI'
import { folderKeys } from './keys'
import { workflowKeys } from '@/features/workflows/hooks/keys'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'
import type { Folder } from '../types/folderTypes'
import type { Workflow } from '@/features/workflows/types/workflowTypes'

/**
 * Hook to fetch all folders for the current workspace.
 */
export function useFolders() {
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  return useQuery({
    queryKey: folderKeys.lists(workspaceId),
    queryFn: ({ signal }) => folderAPI.list(signal),
    enabled: !!workspaceId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

/**
 * Hook to create a new folder.
 */
export function useCreateFolder() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: ({ name, parentId }: { name: string; parentId?: string | null }) =>
      folderAPI.create(name, parentId),
    onSuccess: (newFolder) => {
      queryClient.setQueryData(folderKeys.lists(workspaceId), (oldData: Folder[] | undefined) => {
        return oldData ? [...oldData, newFolder] : [newFolder]
      })
      queryClient.invalidateQueries({ queryKey: folderKeys.lists(workspaceId) })
    },
  })
}

/**
 * Hook to rename/update a folder.
 */
export function useUpdateFolder() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      folderAPI.update(id, name),
    onSuccess: (updatedFolder) => {
      queryClient.setQueryData(folderKeys.lists(workspaceId), (oldData: Folder[] | undefined) => {
        return oldData?.map((f) => (f.id === updatedFolder.id ? updatedFolder : f))
      })
      queryClient.invalidateQueries({ queryKey: folderKeys.lists(workspaceId) })
    },
  })
}

/**
 * Hook to delete a folder.
 */
export function useDeleteFolder() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: (id: string) => folderAPI.delete(id),
    onSuccess: (_, id) => {
      queryClient.setQueryData(folderKeys.lists(workspaceId), (oldData: Folder[] | undefined) => {
        return oldData?.filter((folder) => folder.id !== id)
      })

      // Clean up workflows associated with this folder or its child folders in React Query cache
      queryClient.setQueryData(workflowKeys.lists(workspaceId), (oldData: Workflow[] | undefined) => {
        if (!oldData) return []
        const allFolders = queryClient.getQueryData<Folder[]>(folderKeys.lists(workspaceId)) || []
        
        const getChildFolderIds = (parentFolderId: string): string[] => {
          const children = allFolders.filter(f => f.parent_id === parentFolderId)
          return [parentFolderId, ...children.flatMap(c => getChildFolderIds(c.id))]
        }
        
        const deletedFolderIds = getChildFolderIds(id)
        return oldData.filter(w => !w.folder_id || !deletedFolderIds.includes(w.folder_id))
      })

      queryClient.invalidateQueries({ queryKey: folderKeys.lists(workspaceId) })
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
    },
  })
}

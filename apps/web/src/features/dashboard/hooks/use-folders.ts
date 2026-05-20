import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { requestJson } from '@/lib/api/client'
import { FolderSchema, type Folder, type Workflow } from '@/lib/api/contracts'
import { folderKeys, workflowKeys } from '@/features/dashboard/hooks/keys'
import { useWorkspaceStore } from '@/stores/workspace-store'

const FolderListSchema = z.array(FolderSchema)

/**
 * Hook to fetch all folders for the dashboard.
 */
export function useFolders() {
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  return useQuery({
    queryKey: folderKeys.lists(workspaceId),
    queryFn: async ({ signal }) => {
      return requestJson(FolderListSchema, {
        url: '/folders/',
        method: 'GET',
        signal,
      })
    },
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
    mutationFn: async (name: string) => {
      return requestJson(FolderSchema, {
        url: '/folders/',
        method: 'POST',
        data: { name },
      })
    },
    onSuccess: (newFolder) => {
      queryClient.setQueryData(folderKeys.lists(workspaceId), (oldData: Folder[] | undefined) => {
        return oldData ? [...oldData, newFolder] : [newFolder]
      })
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
    mutationFn: async (id: string) => {
      return requestJson(z.any(), {
        url: `/folders/${id}`,
        method: 'DELETE',
      })
    },
    onSuccess: (_, id) => {
      queryClient.setQueryData(folderKeys.lists(workspaceId), (oldData: Folder[] | undefined) => {
        return oldData?.filter((folder) => folder.id !== id)
      })
      
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
      queryClient.invalidateQueries({ queryKey: workflowKeys.lists(workspaceId) })
    },
  })
}
/**
 * Hook to update an existing folder.
 */
export function useUpdateFolder() {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  return useMutation({
    mutationFn: async ({ id, name }: { id: string; name: string }) => {
      return requestJson(FolderSchema, {
        url: `/folders/${id}`,
        method: 'PUT',
        data: { name },
      })
    },
    onSuccess: (updatedFolder) => {
      queryClient.setQueryData(folderKeys.lists(workspaceId), (oldData: Folder[] | undefined) => {
        return oldData?.map((f) => (f.id === updatedFolder.id ? updatedFolder : f))
      })
    },
  })
}

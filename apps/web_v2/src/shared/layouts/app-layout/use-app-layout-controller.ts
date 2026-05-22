import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useDroppable } from '@dnd-kit/core'
import { useAuth } from '@/features/auth/hooks/useAuth'
import {
  SidebarFolderItem,
  useCreateFolder,
  useDeleteFolder,
  useFolders,
  useUpdateFolder,
} from '@/features/folders'
import {
  useCreateWorkflow,
  useDeleteWorkflow,
  useDuplicateWorkflow,
  useUpdateWorkflow,
  useWorkflowDnD,
  useWorkflows,
} from '@/features/workflows'
import { useFileStats } from '@/features/files/hooks/useFiles'
import { useKBList } from '@/features/knowledge/hooks/useKnowledge'
import { useTables } from '@/features/tables/hooks/useTables'
import { useTablesStore } from '@/features/tables'
import { useWorkspaces, useWorkspaceStore } from '@/features/workspaces'
import { useConfirm, useToast } from '@/shared/components'
import { useTheme } from '@/stores/theme'

export type FolderMenuHandlers = React.ComponentProps<typeof SidebarFolderItem>

export function useAppLayoutController() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const { toast } = useToast()
  const confirm = useConfirm()

  useWorkspaces()

  const { currentWorkspace } = useWorkspaceStore()
  const { data: folders = [], isLoading: isLoadingFolders } = useFolders()
  const { data: workflows = [], isLoading: isLoadingWorkflows } = useWorkflows()
  const { data: knowledgeBases = [] } = useKBList()
  const { data: fileStats } = useFileStats()
  const { data: tables = [] } = useTables()
  const createFolder = useCreateFolder()
  const updateFolder = useUpdateFolder()
  const deleteFolder = useDeleteFolder()
  const createWorkflow = useCreateWorkflow()
  const updateWorkflow = useUpdateWorkflow()
  const deleteWorkflow = useDeleteWorkflow()
  const duplicateWorkflow = useDuplicateWorkflow()
  const { theme, toggle: toggleTheme } = useTheme()

  const [collapsed, setCollapsed] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [shortcutsOpen, setShortcutsOpen] = useState(false)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [feedbackText, setFeedbackText] = useState('')
  const [feedbackSent, setFeedbackSent] = useState(false)
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    Workspace: true,
    Operate: true,
    Workflows: true,
    Data: false,
    Integrations: false,
  })
  const [menuOpen, setMenuOpen] = useState<string | null>(null)
  const [menuPos, setMenuPos] = useState<{ top: number; left: number } | null>(null)
  const [isCreateFolderOpen, setIsCreateFolderOpen] = useState(false)
  const [createFolderName, setCreateFolderName] = useState('')
  const [folderParentId, setFolderParentId] = useState<string | null>(null)
  const [isRenameFolderOpen, setIsRenameFolderOpen] = useState(false)
  const [renameFolderId, setRenameFolderId] = useState('')
  const [renameFolderName, setRenameFolderName] = useState('')
  const [isCreateWorkflowOpen, setIsCreateWorkflowOpen] = useState(false)
  const [createWorkflowName, setCreateWorkflowName] = useState('')
  const [workflowFolderId, setWorkflowFolderId] = useState<string | null>(null)
  const [createWorkflowColor, setCreateWorkflowColor] = useState<string | null>(null)
  const [isRenameWorkflowOpen, setIsRenameWorkflowOpen] = useState(false)
  const [renameWorkflowId, setRenameWorkflowId] = useState('')
  const [renameWorkflowName, setRenameWorkflowName] = useState('')
  const [renameWorkflowColor, setRenameWorkflowColor] = useState<string | null>(null)

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement).tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      if (event.key === '?') setShortcutsOpen(value => !value)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const workflowDnd = useWorkflowDnD({ workflows, folders })
  const { setNodeRef: setRootNodeRef } = useDroppable({
    id: 'workflow-section-root',
    data: { isRoot: true },
  })

  const closeMenus = () => {
    setMenuOpen(null)
    setMenuPos(null)
  }

  const openAnchoredMenu = (event: React.MouseEvent, id: string) => {
    event.stopPropagation()
    event.preventDefault()
    if (menuOpen === id) {
      closeMenus()
      return
    }
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
    setMenuPos({ top: rect.top, left: rect.right + 4 })
    setMenuOpen(id)
  }

  const toggleGroup = (group: string) => {
    setOpenGroups(groups => ({ ...groups, [group]: !groups[group] }))
  }

  const resetCreateFolder = () => {
    setIsCreateFolderOpen(false)
    setCreateFolderName('')
    setFolderParentId(null)
  }

  const resetRenameFolder = () => {
    setIsRenameFolderOpen(false)
    setRenameFolderId('')
    setRenameFolderName('')
  }

  const resetCreateWorkflow = () => {
    setIsCreateWorkflowOpen(false)
    setCreateWorkflowName('')
    setWorkflowFolderId(null)
    setCreateWorkflowColor(null)
  }

  const resetRenameWorkflow = () => {
    setIsRenameWorkflowOpen(false)
    setRenameWorkflowId('')
    setRenameWorkflowName('')
    setRenameWorkflowColor(null)
  }

  const resetFeedback = () => {
    setFeedbackOpen(false)
    setFeedbackSent(false)
    setFeedbackText('')
  }

  const openCreateWorkflow = (folderId?: string | null) => {
    setWorkflowFolderId(folderId ?? null)
    setIsCreateWorkflowOpen(true)
  }

  const openCreateFolder = (parentId?: string | null) => {
    setFolderParentId(parentId ?? null)
    setIsCreateFolderOpen(true)
  }

  const openRenameFolder = (id: string, name: string) => {
    setRenameFolderId(id)
    setRenameFolderName(name)
    setIsRenameFolderOpen(true)
  }

  const openRenameWorkflow = (id: string, name: string, color?: string | null) => {
    setRenameWorkflowId(id)
    setRenameWorkflowName(name)
    setRenameWorkflowColor(color ?? null)
    setIsRenameWorkflowOpen(true)
  }

  const deleteFolderWithConfirm = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: 'Delete Folder',
      message: `Are you sure you want to delete the folder "${name}"? This will not delete its workflows, they will be moved to root.`,
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (!confirmed) return
    deleteFolder.mutate(id, {
      onSuccess: () => toast('Folder deleted successfully', { variant: 'ok' }),
      onError: () => toast('Failed to delete folder', { variant: 'err' }),
    })
  }

  const deleteWorkflowWithConfirm = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: 'Delete Workflow',
      message: `Are you sure you want to delete the workflow "${name}"?`,
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (!confirmed) return
    deleteWorkflow.mutate(id, {
      onSuccess: () => toast('Workflow deleted successfully', { variant: 'ok' }),
      onError: () => toast('Failed to delete workflow', { variant: 'err' }),
    })
  }

  const duplicateWorkflowWithToast = (id: string) => {
    duplicateWorkflow.mutate(id, {
      onSuccess: () => toast('Workflow duplicated successfully', { variant: 'ok' }),
      onError: () => toast('Failed to duplicate workflow', { variant: 'err' }),
    })
  }

  const toggleWorkflowActive = (id: string, isActive: boolean) => {
    updateWorkflow.mutate(
      { id, is_active: isActive },
      {
        onSuccess: () => toast(isActive ? 'Workflow activated' : 'Workflow paused', { variant: 'ok' }),
        onError: () => toast('Failed to update workflow state', { variant: 'err' }),
      }
    )
  }

  const submitCreateFolder = (event: React.FormEvent) => {
    event.preventDefault()
    if (!createFolderName.trim()) return
    createFolder.mutate(
      { name: createFolderName, parentId: folderParentId },
      {
        onSuccess: () => {
          toast('Folder created successfully', { variant: 'ok' })
          resetCreateFolder()
        },
        onError: () => toast('Failed to create folder', { variant: 'err' }),
      }
    )
  }

  const submitRenameFolder = (event: React.FormEvent) => {
    event.preventDefault()
    if (!renameFolderName.trim()) return
    updateFolder.mutate(
      { id: renameFolderId, name: renameFolderName },
      {
        onSuccess: () => {
          toast('Folder renamed successfully', { variant: 'ok' })
          resetRenameFolder()
        },
        onError: () => toast('Failed to rename folder', { variant: 'err' }),
      }
    )
  }

  const submitCreateWorkflow = (event: React.FormEvent) => {
    event.preventDefault()
    createWorkflow.mutate(
      { name: createWorkflowName, folderId: workflowFolderId, color: createWorkflowColor },
      {
        onSuccess: () => {
          toast('Workflow created successfully', { variant: 'ok' })
          resetCreateWorkflow()
        },
        onError: () => toast('Failed to create workflow', { variant: 'err' }),
      }
    )
  }

  const submitRenameWorkflow = (event: React.FormEvent) => {
    event.preventDefault()
    if (!renameWorkflowName.trim()) return
    updateWorkflow.mutate(
      { id: renameWorkflowId, name: renameWorkflowName, color: renameWorkflowColor },
      {
        onSuccess: () => {
          toast('Workflow updated successfully', { variant: 'ok' })
          resetRenameWorkflow()
        },
        onError: () => toast('Failed to update workflow settings', { variant: 'err' }),
      }
    )
  }

  const showPendingFeature = (message: string) => {
    closeMenus()
    toast(message, { variant: 'warn' })
  }

  const pageName = location.pathname.substring(1) || 'dashboard'
  const { selectedTableId } = useTablesStore()
  const selectedTable = pageName === 'tables' ? tables.find(t => t.id === selectedTableId) : null

  const navItemCounts: Record<string, string> = {
    tables: String(tables.length),
    files: String(fileStats?.count ?? 0),
    knowledge: String(knowledgeBases.length),
  }

  return {
    user,
    logout,
    currentWorkspace,
    pageLabel: pageName.charAt(0).toUpperCase() + pageName.slice(1),
    selectedTableName: selectedTable?.name || null,
    theme,
    toggleTheme,
    collapsed,
    setCollapsed,
    profileOpen,
    setProfileOpen,
    shortcutsOpen,
    setShortcutsOpen,
    feedbackOpen,
    setFeedbackOpen,
    feedbackText,
    setFeedbackText,
    feedbackSent,
    setFeedbackSent,
    resetFeedback,
    openGroups,
    toggleGroup,
    menuOpen,
    setMenuOpen,
    menuPos,
    closeMenus,
    openAnchoredMenu,
    folders,
    workflows,
    navItemCounts,
    isLoadingTree: isLoadingFolders || isLoadingWorkflows,
    workflowDnd,
    setRootNodeRef,
    openCreateWorkflow,
    openCreateFolder,
    openRenameFolder,
    openRenameWorkflow,
    deleteFolderWithConfirm,
    deleteWorkflowWithConfirm,
    duplicateWorkflowWithToast,
    toggleWorkflowActive,
    showPendingFeature,
    modalState: {
      isCreateFolderOpen,
      createFolderName,
      setCreateFolderName,
      isRenameFolderOpen,
      renameFolderName,
      setRenameFolderName,
      isCreateWorkflowOpen,
      createWorkflowName,
      setCreateWorkflowName,
      createWorkflowColor,
      setCreateWorkflowColor,
      isRenameWorkflowOpen,
      renameWorkflowName,
      setRenameWorkflowName,
      renameWorkflowColor,
      setRenameWorkflowColor,
      createFolderPending: createFolder.isPending,
      updateFolderPending: updateFolder.isPending,
      createWorkflowPending: createWorkflow.isPending,
      updateWorkflowPending: updateWorkflow.isPending,
      resetCreateFolder,
      resetRenameFolder,
      resetCreateWorkflow,
      resetRenameWorkflow,
      submitCreateFolder,
      submitRenameFolder,
      submitCreateWorkflow,
      submitRenameWorkflow,
    },
  }
}

export type AppLayoutController = ReturnType<typeof useAppLayoutController>

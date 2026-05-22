import { useState, useRef, useCallback, useMemo, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  useSensor,
  useSensors,
  PointerSensor,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from '@dnd-kit/core'
import { arrayMove } from '@dnd-kit/sortable'
import { workflowKeys } from '@/features/workflows/hooks/keys'
import { useBatchUpdateWorkflows } from '@/features/workflows/hooks/useWorkflows'
import { haptics } from '@/shared/utils/haptics'
import { logger } from '@/shared/utils/logger'
import type { WorkflowWithStats } from '@/features/workflows/types/workflowTypes'
import type { Folder } from '@/features/folders/types/folderTypes'
import { useWorkspaceStore } from '@/features/workspaces/store/workspaceStore'

interface UseWorkflowDnDProps {
  workflows: WorkflowWithStats[]
  folders: Folder[]
}

/**
 * Hook to manage drag-and-drop state, sensors, and mutations for workflows and folders in the sidebar.
 */
export function useWorkflowDnD({ workflows, folders }: UseWorkflowDnDProps) {
  const queryClient = useQueryClient()
  const workspaceId = useWorkspaceStore(s => s.currentWorkspaceId)
  const workflowListKey = useMemo(() => workflowKeys.lists(workspaceId), [workspaceId])
  const { mutate: batchUpdate } = useBatchUpdateWorkflows()
  const batchUpdateRef = useRef(batchUpdate)

  useEffect(() => {
    batchUpdateRef.current = batchUpdate
  }, [batchUpdate])

  const [activeDragId, setActiveDragId] = useState<string | null>(null)
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())

  const hoverTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const dragStartWorkflowRef = useRef<WorkflowWithStats | null>(null)
  const lastOverRef = useRef<DragOverEvent['over'] | null>(null)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  const toggleFolder = useCallback((id: string, e?: React.MouseEvent) => {
    e?.stopPropagation()
    setExpandedFolders(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const handleDragStart = useCallback(({ active }: DragStartEvent) => {
    const activeId = active.id.toString().replace('workflow-', '')
    const snap = queryClient.getQueryData<WorkflowWithStats[]>(workflowListKey) || []
    dragStartWorkflowRef.current = snap.find(w => w.id === activeId) || null
    lastOverRef.current = null
    setActiveDragId(active.id.toString())
    haptics.tick()
  }, [queryClient, workflowListKey])

  const handleDragOver = useCallback((event: DragOverEvent) => {
    const { active, over } = event
    if (!over) return

    lastOverRef.current = over

    const activeId = active.id.toString()
    const overId = over.id.toString()

    if (activeId !== overId) haptics.tick()

    const workflow = active.data.current?.workflow as WorkflowWithStats | undefined
    if (!workflow) return

    // Auto-expand folder on hover
    if (overId.startsWith('folder-')) {
      const folderId = overId.replace('folder-', '')
      if (!expandedFolders.has(folderId) && !hoverTimeoutRef.current) {
        hoverTimeoutRef.current = setTimeout(() => {
          setExpandedFolders(prev => {
            const next = new Set(prev)
            next.add(folderId)
            return next
          })
          hoverTimeoutRef.current = null
        }, 400)
      }
    } else {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current)
        hoverTimeoutRef.current = null
      }
    }

    // Resolve target container
    const overWorkflow = over.data.current?.workflow as WorkflowWithStats | undefined
    let overContainerId: string | null | undefined = undefined

    if (overId.startsWith('folder-')) {
      overContainerId = overId.replace('folder-', '')
    } else if (overId === 'workflow-section-root') {
      overContainerId = null
    } else if (overWorkflow) {
      overContainerId = overWorkflow.folder_id ?? null
    } else {
      return
    }

    const isActiveInOverContainer = (workflow.folder_id ?? null) === overContainerId

    if (!isActiveInOverContainer || (overWorkflow && active.id !== over.id)) {
      queryClient.setQueryData(workflowListKey, (old: WorkflowWithStats[] | undefined) => {
        if (!old) return []
        const updated = [...old]
        const activeIdx = updated.findIndex(w => w.id === workflow.id)
        if (activeIdx === -1) return old

        if ((updated[activeIdx].folder_id ?? null) !== overContainerId) {
          updated[activeIdx] = { ...updated[activeIdx], folder_id: overContainerId ?? undefined }
        }

        if (overWorkflow) {
          const overIdx = updated.findIndex(w => w.id === overWorkflow.id)
          if (overIdx !== -1) return arrayMove(updated, activeIdx, overIdx)
        }

        return updated
      })
    }
  }, [expandedFolders, queryClient, workflowListKey])

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)
      hoverTimeoutRef.current = null
    }

    const { active } = event
    const over = event.over ?? lastOverRef.current

    setActiveDragId(null)

    if (!over) {
      // Revert cache to pre-drag state
      logger.warn('DnD: Drop outside droppable, reverting')
      const snapshot = dragStartWorkflowRef.current
      if (snapshot) {
        queryClient.setQueryData(workflowListKey, (old: WorkflowWithStats[] | undefined) => {
          if (!old) return []
          return old.map(w => (w.id === snapshot.id ? snapshot : w))
        })
      }
      dragStartWorkflowRef.current = null
      lastOverRef.current = null
      return
    }

    haptics.snap()

    const activeId = active.id.toString().replace('workflow-', '')
    const overId = over.id.toString()
    const overData = over.data.current

    // Resolve target folder
    let targetFolderId: string | null = null
    if (overData?.isRoot || overId === 'workflow-section-root') {
      targetFolderId = null
    } else if (overData?.folder) {
      targetFolderId = (overData.folder as Folder).id
    } else if (overData?.workflow) {
      targetFolderId = (overData.workflow as WorkflowWithStats).folder_id ?? null
    } else if (overId.startsWith('folder-')) {
      targetFolderId = overId.replace('folder-', '')
    } else {
      targetFolderId = dragStartWorkflowRef.current?.folder_id ?? null
    }

    const currentWorkflows = queryClient.getQueryData<WorkflowWithStats[]>(workflowListKey) || []
    const movedWorkflow = currentWorkflows.find(w => w.id === activeId)

    if (!movedWorkflow) {
      logger.warn('DnD: Moved workflow not found in cache', { activeId })
      dragStartWorkflowRef.current = null
      lastOverRef.current = null
      return
    }

    const originalFolderId = dragStartWorkflowRef.current?.folder_id ?? null

    logger.info('DnD: Committing', {
      workflow: movedWorkflow.name,
      from: originalFolderId,
      to: targetFolderId,
    })

    const workflowsWithoutMoved = currentWorkflows.filter(w => w.id !== activeId)
    const otherWorkflowsInTarget = workflowsWithoutMoved.filter(
      w => (w.folder_id ?? null) === targetFolderId
    )

    const movedWithTarget: WorkflowWithStats = { ...movedWorkflow, folder_id: targetFolderId ?? undefined }

    let targetGroup: WorkflowWithStats[]
    const overWorkflow = overData?.workflow as WorkflowWithStats | undefined

    if (overWorkflow && (overWorkflow.folder_id ?? null) === targetFolderId) {
      const overIdx = otherWorkflowsInTarget.findIndex(w => w.id === overWorkflow.id)
      targetGroup = [...otherWorkflowsInTarget]
      targetGroup.splice(overIdx >= 0 ? overIdx : targetGroup.length, 0, movedWithTarget)
    } else {
      targetGroup = [...otherWorkflowsInTarget, movedWithTarget]
    }

    const originalGroup =
      originalFolderId !== targetFolderId
        ? workflowsWithoutMoved.filter(w => (w.folder_id ?? null) === originalFolderId)
        : []

    const finalUpdates: WorkflowWithStats[] = [
      ...targetGroup.map((w, i) => ({ ...w, position: i })),
      ...originalGroup.map((w, i) => ({ ...w, position: i })),
    ]

    // Apply to cache
    queryClient.setQueryData(workflowListKey, (old: WorkflowWithStats[] | undefined) => {
      if (!old) return []
      return old.map(w => finalUpdates.find(u => u.id === w.id) ?? w)
    })

    // Persist to server
    const updatesToCommit = finalUpdates.map(w => ({
      id: w.id,
      folder_id: w.folder_id ?? null,
      position: w.position ?? 0,
    }))

    batchUpdateRef.current(
      { updates: updatesToCommit },
      {
        onError: (err) => {
          logger.error('DnD: Batch update failed, reverting', { error: String(err) })
          queryClient.invalidateQueries({ queryKey: workflowListKey })
        },
      }
    )

    dragStartWorkflowRef.current = null
    lastOverRef.current = null
  }, [queryClient, workflowListKey])

  const rootWorkflows = useMemo(() => workflows.filter(w => !w.folder_id), [workflows])
  const workflowsByFolder = useMemo(() => {
    const map = new Map<string, WorkflowWithStats[]>()
    folders.forEach(f => map.set(f.id, workflows.filter(w => w.folder_id === f.id)))
    return map
  }, [workflows, folders])

  const activeWorkflowForOverlay = useMemo(() => {
    if (!activeDragId || !activeDragId.startsWith('workflow-')) return null
    const id = activeDragId.replace('workflow-', '')
    return workflows.find(w => w.id === id) || null
  }, [activeDragId, workflows])

  return {
    sensors,
    activeDragId,
    expandedFolders,
    rootWorkflows,
    workflowsByFolder,
    activeWorkflowForOverlay,
    toggleFolder,
    handleDragStart,
    handleDragOver,
    handleDragEnd,
  }
}

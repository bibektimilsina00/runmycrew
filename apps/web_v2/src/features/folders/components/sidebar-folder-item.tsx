import React from 'react'
import { createPortal } from 'react-dom'
import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { SidebarWorkflowItem } from '@/features/workflows/components/sidebar-workflow-item'
import { Icons } from '@/shared/components/icons'
import { cn } from '@/lib/cn'
import type { Folder } from '@/features/folders/types/folderTypes'
import type { WorkflowWithStats } from '@/features/workflows/types/workflowTypes'

interface SidebarFolderItemProps {
  folder: Folder
  allFolders: Folder[]
  allWorkflows: WorkflowWithStats[]
  expandedFolders: Set<string>
  toggleFolder: (id: string, e?: React.MouseEvent) => void
  openMenuId: string | null
  setOpenMenuId: (id: string | null) => void
  onCreateWorkflow: (folderId: string) => void
  onCreateSubfolder: (folderId: string) => void
  onRenameFolder: (id: string, name: string) => void
  onDeleteFolder: (id: string, name: string) => void
  onRenameWorkflow: (id: string, name: string, color: string | null) => void
  onDeleteWorkflow: (id: string, name: string) => void
  onDuplicateWorkflow: (id: string) => void
  onToggleWorkflowActive: (id: string, isActive: boolean) => void
}

export function SidebarFolderItem({
  folder,
  allFolders,
  allWorkflows,
  expandedFolders,
  toggleFolder,
  openMenuId,
  setOpenMenuId,
  onCreateWorkflow,
  onCreateSubfolder,
  onRenameFolder,
  onDeleteFolder,
  onRenameWorkflow,
  onDeleteWorkflow,
  onDuplicateWorkflow,
  onToggleWorkflowActive,
}: SidebarFolderItemProps) {
  const open = expandedFolders.has(folder.id)
  const childFolders = allFolders.filter(f => f.parent_id === folder.id)
  const folderWorkflows = allWorkflows.filter(w => w.folder_id === folder.id)
  const [menuPos, setMenuPos] = React.useState<{ top: number; left: number } | null>(null)

  const { setNodeRef, isOver } = useDroppable({
    id: `folder-${folder.id}`,
    data: { folder },
  })

  const isMenuOpen = openMenuId === `folder-${folder.id}`

  const handleMoreClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    const menuId = `folder-${folder.id}`
    if (isMenuOpen) {
      setOpenMenuId(null)
      setMenuPos(null)
    } else {
      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
      setMenuPos({ top: rect.top, left: rect.right + 4 })
      setOpenMenuId(menuId)
    }
  }

  const closeMenu = () => {
    setOpenMenuId(null)
    setMenuPos(null)
  }

  return (
    <div className="relative group-data-[collapsed=true]/shell:hidden group/folder">
      <div
        ref={setNodeRef}
        className={cn(
          "flex items-center gap-[8px] p-[6px] rounded-[8px] text-[12.5px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)]",
          isOver && "bg-[oklch(from_var(--accent)_l_c_h_/_0.15)] text-[var(--accent)] scale-[1.02]"
        )}
        onClick={(e) => toggleFolder(folder.id, e)}
      >
        <span
          className={cn(
            "w-[12px] h-[12px] inline-flex items-center justify-center transition-transform duration-140 text-[var(--text-faint)] shrink-0 [&_svg]:w-[10px] [&_svg]:h-[10px]",
            open ? "" : "-rotate-90"
          )}
        >
          <Icons.Caret />
        </span>
        <span className="inline-flex text-[var(--text-mute)] shrink-0 [&_svg]:w-[14px] [&_svg]:h-[14px]">
          {open ? <Icons.FolderOpen /> : <Icons.Folder />}
        </span>
        <span className="flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis tracking-tight">
          {folder.name}
        </span>
        {(folderWorkflows.length > 0 || childFolders.length > 0) && (
          <span className="font-mono text-[10px] text-[var(--text-faint)] font-medium px-[2px]">
            {folderWorkflows.length}
          </span>
        )}
        <button
          className={cn(
            "w-[22px] h-[22px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center opacity-0 transition-all duration-100 shrink-0 hover:bg-[var(--surface-2)] hover:text-[var(--text)] group-hover/folder:opacity-100 [&_svg]:w-[13px] [&_svg]:h-[13px]",
            isMenuOpen && "opacity-100 bg-[var(--surface-2)] text-[var(--text)]"
          )}
          onClick={handleMoreClick}
          onPointerDown={(e) => e.stopPropagation()}
          title="More"
        >
          <Icons.More />
        </button>
      </div>

      {open && (
        <div className="pl-[14px] flex flex-col relative before:content-[''] before:absolute before:left-[11px] before:top-[4px] before:bottom-[4px] before:w-[1px] before:bg-[var(--border-faint)]">
          {childFolders.map((child) => (
            <SidebarFolderItem
              key={child.id}
              folder={child}
              allFolders={allFolders}
              allWorkflows={allWorkflows}
              expandedFolders={expandedFolders}
              toggleFolder={toggleFolder}
              openMenuId={openMenuId}
              setOpenMenuId={setOpenMenuId}
              onCreateWorkflow={onCreateWorkflow}
              onCreateSubfolder={onCreateSubfolder}
              onRenameFolder={onRenameFolder}
              onDeleteFolder={onDeleteFolder}
              onRenameWorkflow={onRenameWorkflow}
              onDeleteWorkflow={onDeleteWorkflow}
              onDuplicateWorkflow={onDuplicateWorkflow}
              onToggleWorkflowActive={onToggleWorkflowActive}
            />
          ))}

          {folderWorkflows.length > 0 && (
            <SortableContext
              items={folderWorkflows.map((w) => `workflow-${w.id}`)}
              strategy={verticalListSortingStrategy}
            >
              {folderWorkflows.map((wf) => (
                <SidebarWorkflowItem
                  key={wf.id}
                  workflow={wf}
                  onRename={onRenameWorkflow}
                  onDelete={onDeleteWorkflow}
                  onDuplicate={onDuplicateWorkflow}
                  onToggleActive={onToggleWorkflowActive}
                  openMenuId={openMenuId}
                  setOpenMenuId={setOpenMenuId}
                />
              ))}
            </SortableContext>
          )}
        </div>
      )}

      {isMenuOpen && menuPos && createPortal(
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 9998 }}
            onClick={(e) => {
              e.stopPropagation()
              closeMenu()
            }}
            onPointerDown={(e) => e.stopPropagation()}
          />
          <div
            className="w-[240px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in zoom-in-95 duration-100"
            style={{ position: 'fixed', top: menuPos.top, left: menuPos.left, zIndex: 9999 }}
            onClick={(e) => e.stopPropagation()}
            onPointerDown={(e) => e.stopPropagation()}
          >
            <button
              className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
              onClick={(e) => {
                e.stopPropagation()
                closeMenu()
                onCreateWorkflow(folder.id)
              }}
            >
              <Icons.Plus /> New workflow in folder
            </button>
            <button
              className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
              onClick={(e) => {
                e.stopPropagation()
                closeMenu()
                onCreateSubfolder(folder.id)
              }}
            >
              <Icons.Folder /> New subfolder
            </button>
            <button
              className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0"
              onClick={(e) => {
                e.stopPropagation()
                closeMenu()
                onRenameFolder(folder.id, folder.name)
              }}
            >
              <Icons.Edit /> Rename folder
            </button>
            <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
            <button
              className="flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0 text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.10)]"
              onClick={(e) => {
                e.stopPropagation()
                closeMenu()
                onDeleteFolder(folder.id, folder.name)
              }}
            >
              <Icons.Trash /> Delete folder
            </button>
          </div>
        </>,
        document.body
      )}
    </div>
  )
}

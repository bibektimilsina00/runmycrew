import { DndContext } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { NavLink } from 'react-router-dom'
import { SidebarFolderItem } from '@/features/folders'
import { SidebarWorkflowItem, WorkflowDragOverlay } from '@/features/workflows'
import { WorkspaceSelector } from '@/features/workspaces'
import { cn } from '@/lib/cn'
import { Spinner } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import type { AppLayoutController } from './use-app-layout-controller'
import { ACTIVE_NAV_LINK_CLASS, MENU_ITEM_CLASS, NAV_GROUPS, NAV_LINK_CLASS } from './navigation'
import { DropdownMenu } from './dropdown-menu'

interface AppSidebarProps {
  controller: AppLayoutController
}

export function AppSidebar({ controller }: AppSidebarProps) {
  const {
    collapsed,
    setCollapsed,
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
    isLoadingTree,
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
  } = controller

  return (
    <aside className="relative h-[calc(100vh-28px)] my-[14px] ml-[14px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] flex flex-col overflow-hidden shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)] z-20">
      <SidebarHeader collapsed={collapsed} onToggleCollapsed={() => setCollapsed(value => !value)} />

      <div className="flex-1 min-h-0 overflow-y-auto pt-[8px] px-[10px] pb-[10px] flex flex-col gap-0 [&::-webkit-scrollbar]:hidden [scrollbar-width:none] group-data-[collapsed=true]/shell:px-[8px]">
        {NAV_GROUPS.map((section, index) => (
          <div
            key={section.group}
            className={cn(
              'flex flex-col gap-[1px] pb-[4px] group-data-[collapsed=true]/shell:pb-[6px] group-data-[collapsed=true]/shell:border-t group-data-[collapsed=true]/shell:border-[var(--border-faint)] group-data-[collapsed=true]/shell:pt-[6px] first:border-none first:pt-0',
              !openGroups[section.group] && 'pb-0',
              section.isWorkflows && 'relative'
            )}
          >
            <SidebarGroupHeader
              sectionName={section.group}
              isWorkflows={section.isWorkflows}
              workflowCount={workflows.length}
              onToggle={() => toggleGroup(section.group)}
              onOpenMenu={event => openAnchoredMenu(event, 'group')}
              onCreateWorkflow={() => openCreateWorkflow()}
              menuOpen={menuOpen}
            />

            {openGroups[section.group] && !section.isWorkflows && section.items?.map(item => (
              <NavLink
                key={item.id}
                to={item.to}
                className={({ isActive }) => cn(NAV_LINK_CLASS, isActive && item.to !== '#' && ACTIVE_NAV_LINK_CLASS)}
                title={item.label}
              >
                <item.icon />
                <span className="flex-1 group-data-[collapsed=true]/shell:hidden">{item.label}</span>
                {(navItemCounts[item.id] ?? item.count) && (
                  <span className="ml-auto font-mono text-[10.5px] text-[var(--text-faint)] font-medium group-data-[collapsed=true]/shell:hidden">
                    {navItemCounts[item.id] ?? item.count}
                  </span>
                )}
              </NavLink>
            ))}

            {openGroups[section.group] && section.isWorkflows && (
              <DndContext
                sensors={workflowDnd.sensors}
                onDragStart={workflowDnd.handleDragStart}
                onDragOver={workflowDnd.handleDragOver}
                onDragEnd={workflowDnd.handleDragEnd}
              >
                <WorkflowTree
                  folders={folders}
                  workflows={workflows}
                  rootWorkflows={workflowDnd.rootWorkflows}
                  expandedFolders={workflowDnd.expandedFolders}
                  isLoading={isLoadingTree}
                  menuOpen={menuOpen}
                  setMenuOpen={setMenuOpen}
                  setRootNodeRef={setRootNodeRef}
                  toggleFolder={workflowDnd.toggleFolder}
                  onCreateWorkflow={openCreateWorkflow}
                  onCreateFolder={openCreateFolder}
                  onRenameFolder={openRenameFolder}
                  onDeleteFolder={deleteFolderWithConfirm}
                  onRenameWorkflow={openRenameWorkflow}
                  onDeleteWorkflow={deleteWorkflowWithConfirm}
                  onDuplicateWorkflow={duplicateWorkflowWithToast}
                  onToggleWorkflowActive={toggleWorkflowActive}
                />
                <WorkflowDragOverlay activeWorkflow={workflowDnd.activeWorkflowForOverlay} />
              </DndContext>
            )}

            {index === NAV_GROUPS.length - 1 && (
              <GroupActionsMenu
                activeId={menuOpen}
                position={menuPos}
                onClose={closeMenus}
                onCreateWorkflow={() => {
                  closeMenus()
                  openCreateWorkflow()
                }}
                onCreateFolder={() => {
                  closeMenus()
                  openCreateFolder()
                }}
                onImport={() => showPendingFeature('Import feature not implemented yet')}
                onExport={() => showPendingFeature('Export all feature not implemented yet')}
                onSort={() => showPendingFeature('Sorting not implemented yet')}
              />
            )}
          </div>
        ))}
      </div>

      <div className="shrink-0 p-[8px] border-t border-[var(--border-faint)] flex gap-[4px] group-data-[collapsed=true]/shell:hidden">
        <button className="flex-1 inline-flex items-center justify-center gap-[6px] py-[7px] px-[8px] rounded-[7px] text-[12px] text-[var(--text-mute)] font-medium transition-colors duration-100 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]" type="button"><Icons.Help /> Help &amp; docs</button>
        <button className="flex-1 inline-flex items-center justify-center gap-[6px] py-[7px] px-[8px] rounded-[7px] text-[12px] text-[var(--text-mute)] font-medium transition-colors duration-100 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]" type="button"><Icons.Feedback /> Feedback</button>
      </div>
    </aside>
  )
}

function SidebarHeader({ collapsed, onToggleCollapsed }: { collapsed: boolean; onToggleCollapsed: () => void }) {
  return (
    <div className="shrink-0 pt-[14px] px-[10px] pb-[12px] flex flex-col gap-[12px] border-b border-[var(--border-faint)] group-data-[collapsed=true]/shell:pt-[14px] group-data-[collapsed=true]/shell:px-[8px] group-data-[collapsed=true]/shell:pb-[12px] group-data-[collapsed=true]/shell:gap-[10px]">
      <div className="flex items-center justify-between py-[2px] px-[6px] pb-[4px] group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:flex-col group-data-[collapsed=true]/shell:gap-[10px] group-data-[collapsed=true]/shell:px-[4px]">
        <span className="inline-flex items-center gap-[9px] text-[15px] font-semibold tracking-tight text-[var(--text)] group-data-[collapsed=true]/shell:gap-0">
          <span className="w-[22px] h-[22px] inline-flex items-center justify-center rounded-[6px] bg-[var(--text)] text-[var(--bg)]"><Icons.FuseMark style={{ width: 14, height: 14 }} /></span>
          <span className="inline group-data-[collapsed=true]/shell:hidden">fuse</span>
          <span className="font-mono text-[9.5px] tracking-[0.14em] uppercase text-[var(--text-faint)] border border-[var(--border-soft)] py-[2px] px-[6px] pb-[1px] rounded-[4px] ml-[6px] group-data-[collapsed=true]/shell:hidden">Beta</span>
        </span>
        <button
          className="w-[24px] h-[24px] rounded-[6px] text-[var(--text-faint)] inline-flex items-center justify-center hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]"
          onClick={onToggleCollapsed}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <Icons.PanelOpen /> : <Icons.PanelClose />}
        </button>
      </div>

      <WorkspaceSelector />

      <div className="flex items-center gap-[8px] px-[10px] h-[34px] rounded-[9px] bg-[var(--bg)] border border-[var(--border-faint)] transition-colors duration-120 w-full min-w-0 hover:border-[var(--border-soft)] focus-within:border-[var(--border)] focus-within:bg-[var(--surface)] [&>svg]:w-[14px] [&>svg]:h-[14px] [&>svg]:text-[var(--text-faint)] [&>svg]:shrink-0 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:px-0 group-data-[collapsed=true]/shell:gap-0">
        <Icons.Search />
        <input placeholder="Search" className="bg-transparent border-none outline-none flex-1 min-w-0 text-[13px] text-[var(--text)] tracking-tight p-0 placeholder:text-[var(--text-faint)] group-data-[collapsed=true]/shell:hidden" />
        <span className="kbd group-data-[collapsed=true]/shell:hidden">⌘K</span>
      </div>
    </div>
  )
}

interface SidebarGroupHeaderProps {
  sectionName: string
  isWorkflows?: boolean
  workflowCount: number
  menuOpen: string | null
  onToggle: () => void
  onOpenMenu: (event: React.MouseEvent) => void
  onCreateWorkflow: () => void
}

function SidebarGroupHeader({
  sectionName,
  isWorkflows,
  workflowCount,
  menuOpen,
  onToggle,
  onOpenMenu,
  onCreateWorkflow,
}: SidebarGroupHeaderProps) {
  return (
    <div className="flex items-center gap-[6px] pt-[8px] px-[10px] pb-[4px] font-mono text-[10px] tracking-widest uppercase text-[var(--text-dim)] font-medium cursor-pointer w-full text-left transition-colors duration-100 hover:text-[var(--text-mute)] group-data-[collapsed=true]/shell:hidden relative" onClick={onToggle}>
      <span className="inline-flex w-[12px] h-[12px] transition-transform duration-160 [&_svg]:w-[11px] [&_svg]:h-[11px]"><Icons.Caret /></span>
      <span className="flex-1">{sectionName}</span>
      {isWorkflows && (
        <>
          <span className="font-mono text-[9.5px] text-[var(--text-faint)] ml-[4px] font-medium">{workflowCount}</span>
          <button
            className={cn(
              'w-[20px] h-[20px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center transition-colors duration-100 shrink-0 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[12px] [&_svg]:h-[12px]',
              menuOpen === 'group' && 'bg-[var(--surface-2)] text-[var(--text)]'
            )}
            onClick={onOpenMenu}
            title="More"
          >
            <Icons.More />
          </button>
          <button
            className="w-[20px] h-[20px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center transition-colors duration-100 shrink-0 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[12px] [&_svg]:h-[12px]"
            title="New workflow"
            onClick={event => {
              event.stopPropagation()
              onCreateWorkflow()
            }}
          >
            <Icons.Plus />
          </button>
        </>
      )}
    </div>
  )
}

interface WorkflowTreeProps {
  folders: AppLayoutController['folders']
  workflows: AppLayoutController['workflows']
  rootWorkflows: AppLayoutController['workflowDnd']['rootWorkflows']
  expandedFolders: AppLayoutController['workflowDnd']['expandedFolders']
  isLoading: boolean
  menuOpen: string | null
  setMenuOpen: (id: string | null) => void
  setRootNodeRef: (element: HTMLElement | null) => void
  toggleFolder: (id: string) => void
  onCreateWorkflow: (folderId?: string | null) => void
  onCreateFolder: (parentId?: string | null) => void
  onRenameFolder: (id: string, name: string) => void
  onDeleteFolder: (id: string, name: string) => void
  onRenameWorkflow: (id: string, name: string, color?: string | null) => void
  onDeleteWorkflow: (id: string, name: string) => void
  onDuplicateWorkflow: (id: string) => void
  onToggleWorkflowActive: (id: string, isActive: boolean) => void
}

function WorkflowTree({
  folders,
  workflows,
  rootWorkflows,
  expandedFolders,
  isLoading,
  menuOpen,
  setMenuOpen,
  setRootNodeRef,
  toggleFolder,
  onCreateWorkflow,
  onCreateFolder,
  onRenameFolder,
  onDeleteFolder,
  onRenameWorkflow,
  onDeleteWorkflow,
  onDuplicateWorkflow,
  onToggleWorkflowActive,
}: WorkflowTreeProps) {
  return (
    <div ref={setRootNodeRef} className="flex flex-col gap-[1px] group-data-[collapsed=true]/shell:hidden">
      {isLoading ? (
        <div className="flex items-center justify-center py-4">
          <Spinner />
        </div>
      ) : folders.length === 0 && workflows.length === 0 ? (
        <div className="text-center py-3 text-[11px] text-[var(--text-mute)]">No folders or workflows</div>
      ) : (
        <>
          {folders
            .filter(folder => !folder.parent_id || !folders.some(parent => parent.id === folder.parent_id))
            .map(folder => (
              <SidebarFolderItem
                key={folder.id}
                folder={folder}
                allFolders={folders}
                allWorkflows={workflows}
                expandedFolders={expandedFolders}
                toggleFolder={toggleFolder}
                openMenuId={menuOpen}
                setOpenMenuId={setMenuOpen}
                onCreateWorkflow={onCreateWorkflow}
                onCreateSubfolder={onCreateFolder}
                onRenameFolder={onRenameFolder}
                onDeleteFolder={onDeleteFolder}
                onRenameWorkflow={onRenameWorkflow}
                onDeleteWorkflow={onDeleteWorkflow}
                onDuplicateWorkflow={onDuplicateWorkflow}
                onToggleWorkflowActive={onToggleWorkflowActive}
              />
            ))}

          {rootWorkflows.length > 0 && (
            <SortableContext items={rootWorkflows.map(workflow => `workflow-${workflow.id}`)} strategy={verticalListSortingStrategy}>
              {rootWorkflows.map(workflow => (
                <SidebarWorkflowItem
                  key={workflow.id}
                  workflow={workflow}
                  onRename={onRenameWorkflow}
                  onDelete={onDeleteWorkflow}
                  onDuplicate={onDuplicateWorkflow}
                  onToggleActive={onToggleWorkflowActive}
                  openMenuId={menuOpen}
                  setOpenMenuId={setMenuOpen}
                />
              ))}
            </SortableContext>
          )}
        </>
      )}
    </div>
  )
}

function GroupActionsMenu({
  activeId,
  position,
  onClose,
  onCreateWorkflow,
  onCreateFolder,
  onImport,
  onExport,
  onSort,
}: {
  activeId: string | null
  position: { top: number; left: number } | null
  onClose: () => void
  onCreateWorkflow: () => void
  onCreateFolder: () => void
  onImport: () => void
  onExport: () => void
  onSort: () => void
}) {
  return (
    <DropdownMenu id="group" activeId={activeId} position={position} onClose={onClose}>
      <button className={MENU_ITEM_CLASS} onClick={onCreateWorkflow}><Icons.Plus /> New workflow</button>
      <button className={MENU_ITEM_CLASS} onClick={onCreateFolder}><Icons.Folder /> Create folder</button>
      <button className={MENU_ITEM_CLASS} onClick={onImport}><Icons.Doc /> Import workflow</button>
      <button className={MENU_ITEM_CLASS} onClick={onExport}><Icons.Download /> Export all</button>
      <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
      <button className={MENU_ITEM_CLASS} onClick={onSort}><Icons.Sort /> Sort A → Z</button>
    </DropdownMenu>
  )
}

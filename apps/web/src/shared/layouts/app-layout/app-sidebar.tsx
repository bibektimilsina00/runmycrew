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
import { NAV_GROUPS } from './navigation'
import { DropdownMenu } from './dropdown-menu'

interface AppSidebarProps {
  controller: AppLayoutController
  variant?: 'floating' | 'flat'
}

/** Base class for all nav items — used by NavLink, workflow and folder rows */
const NAV_ITEM =
  'flex items-center gap-[10px] py-[6px] px-[10px] rounded-[8px] text-[13px] font-medium text-[var(--text-mute)] w-full cursor-pointer transition-all duration-200 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[15px] [&_svg]:h-[15px] [&_svg]:shrink-0 [&_svg]:text-current [&_svg]:opacity-80 relative no-underline group-data-[collapsed=true]/shell:w-[36px] group-data-[collapsed=true]/shell:h-[36px] group-data-[collapsed=true]/shell:p-0 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:mx-auto'

const NAV_ITEM_ACTIVE =
  "bg-[var(--surface)] text-[var(--text)] [&_svg]:opacity-100"

const SECTION_HEADER =
  'flex items-center gap-[6px] px-[10px] pt-[6px] pb-[4px] select-none group-data-[collapsed=true]/shell:hidden'

const ACTION_BTN =
  'w-[20px] h-[20px] rounded-[5px] inline-flex items-center justify-center text-[var(--text-faint)] transition-colors duration-100 shrink-0 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[12px] [&_svg]:h-[12px]'

const MENU_ITEM =
  'flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0'

export function AppSidebar({ controller, variant = 'floating' }: AppSidebarProps) {
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

  const isFlat = variant === 'flat'

  return (
    <aside
      className={cn(
        'relative flex flex-col overflow-hidden transition-all duration-300 ease-in-out z-20',
        isFlat
          ? 'h-screen bg-[var(--bg-2)] border-r border-[var(--border-faint)]'
          : 'h-[calc(100vh-28px)] my-[14px] mx-[14px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)]'
      )}
    >
      <SidebarHeader collapsed={collapsed} onToggleCollapsed={() => setCollapsed(value => !value)} />

      {/* ── Nav scroll area ─────────────────────────────────── */}
      <div className="flex-1 min-h-0 overflow-y-auto px-[8px] pb-[8px] flex flex-col [&::-webkit-scrollbar]:hidden [scrollbar-width:none] group-data-[collapsed=true]/shell:px-[6px]">
        {NAV_GROUPS.map((section, index) => (
          <div
            key={section.group}
            className={cn(
              'flex flex-col',
              section.isWorkflows && 'relative flex-1',
              index > 0 && 'mt-[4px] pt-[8px] border-t border-[var(--border-faint)] group-data-[collapsed=true]/shell:border-none group-data-[collapsed=true]/shell:mt-0 group-data-[collapsed=true]/shell:pt-0'
            )}
          >
            {/* Section header */}
            <button
              type="button"
              className={cn(
                SECTION_HEADER,
                'text-left w-full cursor-pointer group-data-[collapsed=true]/shell:hidden'
              )}
              onClick={() => toggleGroup(section.group)}
            >
              <span
                className={cn(
                  'inline-flex w-[13px] h-[13px] text-[var(--text-mute)] transition-transform duration-150 [&_svg]:w-[12px] [&_svg]:h-[12px]',
                  !openGroups[section.group] && '-rotate-90'
                )}
              >
                <Icons.Caret />
              </span>
              <span className="flex-1 text-[12.5px] text-[var(--text)] font-bold tracking-tight">
                {section.group}
              </span>
              {section.isWorkflows && (
                <>
                  <span className="font-mono text-[9.5px] text-[var(--text-faint)] font-medium">
                    {workflows.length}
                  </span>
                  <span
                    role="button"
                    tabIndex={0}
                    className={cn(
                      ACTION_BTN,
                      menuOpen === 'group' && 'bg-[var(--surface-2)] text-[var(--text)]'
                    )}
                    onClick={e => openAnchoredMenu(e, 'group')}
                    onKeyDown={e => e.key === 'Enter' && openAnchoredMenu(e as unknown as React.MouseEvent, 'group')}
                    title="More options"
                    aria-label="More workflow options"
                  >
                    <Icons.More />
                  </span>
                  <span
                    role="button"
                    tabIndex={0}
                    className={ACTION_BTN}
                    title="New workflow"
                    aria-label="Create new workflow"
                    onClick={event => {
                      event.stopPropagation()
                      openCreateWorkflow()
                    }}
                    onKeyDown={e => {
                      if (e.key === 'Enter') { e.stopPropagation(); openCreateWorkflow() }
                    }}
                  >
                    <Icons.Plus />
                  </span>
                </>
              )}
            </button>

            {/* Nav items */}
            <div
              className={cn(
                'grid transition-[grid-template-rows] duration-200 ease-in-out',
                openGroups[section.group] ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
              )}
            >
              <div className="overflow-hidden min-h-0 pl-[14px] group-data-[collapsed=true]/shell:pl-0 flex flex-col gap-[2px]">
                {!section.isWorkflows && section.items?.map(item => (
                  <NavLink
                    key={item.id}
                    to={item.to}
                    className={({ isActive }) => cn(NAV_ITEM, isActive && item.to !== '#' && NAV_ITEM_ACTIVE)}
                    title={item.label}
                  >
                    <item.icon />
                    <span className="flex-1 group-data-[collapsed=true]/shell:hidden">{item.label}</span>
                    {navItemCounts[item.id] && (
                      <span className="ml-auto font-mono text-[10.5px] text-[var(--text-faint)] font-medium tabular-nums group-data-[collapsed=true]/shell:hidden">
                        {navItemCounts[item.id]}
                      </span>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>

            {/* Workflow tree */}
            <div
              className={cn(
                'grid transition-[grid-template-rows] duration-200 ease-in-out',
                openGroups[section.group] ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
              )}
            >
              <div className="overflow-hidden min-h-0 pl-[14px] group-data-[collapsed=true]/shell:pl-0">
                {section.isWorkflows && (
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
              </div>
            </div>

            {index === NAV_GROUPS.length - 1 && (
              <GroupActionsMenu
                activeId={menuOpen}
                position={menuPos}
                onClose={closeMenus}
                onCreateWorkflow={() => { closeMenus(); openCreateWorkflow() }}
                onCreateFolder={() => { closeMenus(); openCreateFolder() }}
                onImport={() => showPendingFeature('Import feature not implemented yet')}
                onExport={() => showPendingFeature('Export all feature not implemented yet')}
                onSort={() => showPendingFeature('Sorting not implemented yet')}
              />
            )}
          </div>
        ))}
      </div>

      {/* ── Footer ──────────────────────────────────────────── */}
      <div className="shrink-0 h-[36px] px-[8px] border-t border-[var(--border-faint)] flex items-center gap-[2px] group-data-[collapsed=true]/shell:hidden">
        <button
          className="flex-1 h-[24px] inline-flex items-center justify-center gap-[6px] px-[8px] rounded-[7px] text-[12px] text-[var(--text-faint)] font-medium transition-colors duration-100 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]"
          type="button"
        >
          <Icons.Help />
          <span>Help & docs</span>
        </button>
        <button
          className="flex-1 h-[24px] inline-flex items-center justify-center gap-[6px] px-[8px] rounded-[7px] text-[12px] text-[var(--text-faint)] font-medium transition-colors duration-100 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]"
          type="button"
        >
          <Icons.Feedback />
          <span>Feedback</span>
        </button>
      </div>
    </aside>
  )
}

/* ── Sidebar header ─────────────────────────────────────────────────────────── */
function SidebarHeader({ collapsed, onToggleCollapsed }: { collapsed: boolean; onToggleCollapsed: () => void }) {
  return (
    <div className="shrink-0 px-[12px] pt-[14px] pb-[10px] flex flex-col gap-[10px] border-b border-[var(--border-faint)] group-data-[collapsed=true]/shell:px-[8px] group-data-[collapsed=true]/shell:py-[14px] group-data-[collapsed=true]/shell:gap-[10px]">
      {/* Logo row */}
      <div className="flex items-center justify-between group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:w-full">
        <span className="inline-flex items-center gap-[8px] text-[14px] font-semibold tracking-tight text-[var(--text)] group-data-[collapsed=true]/shell:hidden">
          <span className="w-[22px] h-[22px] inline-flex items-center justify-center rounded-[6px] bg-[var(--text)] text-[var(--bg)] shrink-0">
            <Icons.FuseMark style={{ width: 13, height: 13 }} />
          </span>
          <span>fuse</span>
        </span>
        <button
          className="rounded-[6px] text-[var(--text-faint)] inline-flex items-center justify-center transition-all duration-200 shrink-0 w-[24px] h-[24px] hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px] group-data-[collapsed=true]/shell:w-[32px] group-data-[collapsed=true]/shell:h-[32px] group-data-[collapsed=true]/shell:relative group-data-[collapsed=true]/shell:mx-auto group-data-[collapsed=true]/shell:bg-transparent group-data-[collapsed=true]/shell:hover:bg-[var(--surface)] group-data-[collapsed=true]/shell:hover:text-[var(--text)] group-data-[collapsed=true]/shell:p-0"
          onClick={onToggleCollapsed}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <span className="group-data-[collapsed=true]/shell:hidden flex items-center justify-center">
            {collapsed ? <Icons.PanelOpen /> : <Icons.PanelClose />}
          </span>
          <span className="hidden group-data-[collapsed=true]/shell:flex items-center justify-center w-full h-full relative group/btn">
            <span className="w-[22px] h-[22px] inline-flex items-center justify-center rounded-[6px] bg-[var(--text)] text-[var(--bg)] absolute transition-all duration-150 group-hover/btn:opacity-0 group-hover/btn:scale-75">
              <Icons.FuseMark style={{ width: 13, height: 13 }} />
            </span>
            <span className="absolute opacity-0 scale-75 transition-all duration-150 group-hover/btn:opacity-100 group-hover/btn:scale-100 text-[var(--text-faint)] group-hover/btn:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px]">
              {collapsed ? <Icons.PanelOpen /> : <Icons.PanelClose />}
            </span>
          </span>
        </button>
      </div>

      {/* Workspace selector with separating gap */}
      <div className="mt-[4px] group-data-[collapsed=true]/shell:mt-0">
        <WorkspaceSelector />
      </div>

      {/* Search bar */}
      <div className="flex items-center gap-[8px] px-[10px] h-[32px] rounded-[8px] bg-[var(--bg)] border border-[var(--border-faint)] transition-all duration-120 w-full min-w-0 hover:border-[var(--border-soft)] focus-within:border-[var(--border)] focus-within:bg-[var(--surface)] [&>svg]:w-[13px] [&>svg]:h-[13px] [&>svg]:text-[var(--text-faint)] [&>svg]:shrink-0 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:px-0 group-data-[collapsed=true]/shell:gap-0 group-data-[collapsed=true]/shell:w-[36px] group-data-[collapsed=true]/shell:h-[36px] group-data-[collapsed=true]/shell:mx-auto">
        <Icons.Search />
        <input
          placeholder="Search"
          className="bg-transparent border-none outline-none flex-1 min-w-0 text-[12.5px] text-[var(--text)] tracking-tight p-0 placeholder:text-[var(--text-dim)] group-data-[collapsed=true]/shell:hidden"
        />
        <span className="kbd group-data-[collapsed=true]/shell:hidden">⌘K</span>
      </div>
    </div>
  )
}

/* ── Workflow tree ──────────────────────────────────────────────────────────── */
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
        <div className="flex items-center justify-center py-6">
          <Spinner />
        </div>
      ) : folders.length === 0 && workflows.length === 0 ? (
        <div className="mx-[2px] mt-[2px] flex flex-col items-center justify-center gap-[6px] py-[20px] px-[12px] rounded-[8px] border border-dashed border-[var(--border-faint)]">
          <span className="text-[11px] text-[var(--text-faint)] text-center leading-relaxed">
            No workflows yet
          </span>
        </div>
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

/* ── Group actions menu ─────────────────────────────────────────────────────── */
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
      <button className={MENU_ITEM} onClick={onCreateWorkflow}><Icons.Plus /> New workflow</button>
      <button className={MENU_ITEM} onClick={onCreateFolder}><Icons.Folder /> Create folder</button>
      <button className={MENU_ITEM} onClick={onImport}><Icons.Doc /> Import workflow</button>
      <button className={MENU_ITEM} onClick={onExport}><Icons.Download /> Export all</button>
      <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
      <button className={MENU_ITEM} onClick={onSort}><Icons.Sort /> Sort A → Z</button>
    </DropdownMenu>
  )
}

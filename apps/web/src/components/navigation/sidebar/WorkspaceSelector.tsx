import React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ChevronDown, Plus, UserPlus } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { switchWorkspace, useCreateWorkspace } from '@/features/workspaces/hooks'
import { folderKeys, workflowKeys } from '@/features/dashboard/hooks/keys'
import { cn } from '@/lib/utils'
import { useWorkspaceStore } from '@/stores/workspace-store'

interface WorkspaceSelectorProps {
  isCollapsed: boolean
}

export const WorkspaceSelector: React.FC<WorkspaceSelectorProps> = ({ isCollapsed }) => {
  const [open, setOpen] = React.useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const createWorkspace = useCreateWorkspace()
  const { currentWorkspace, currentWorkspaceId, workspaces } = useWorkspaceStore()
  const label = currentWorkspace?.name ?? 'Workspace'
  const initial = label[0]?.toUpperCase() ?? '?'

  const handleCreateWorkspace = () => {
    const name = window.prompt('Workspace name')
    if (!name?.trim()) return
    createWorkspace.mutate(name.trim(), {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: workflowKeys.all })
        queryClient.invalidateQueries({ queryKey: folderKeys.all })
        if (location.pathname.startsWith('/workflows/')) {
          navigate('/workflows')
        }
        setOpen(false)
      },
    })
  }

  return (
    <div className="relative mb-2.5 flex-shrink-0 pr-2.5 pl-[9px] overflow-visible">
      <button
        onClick={() => setOpen(value => !value)}
        className={cn(
          "flex h-8 w-full items-center gap-2 rounded-lg border border-white/5 bg-[var(--surface-2)] pl-[5px] pr-2 text-left transition-colors hover:bg-[var(--surface-hover)] group",
          isCollapsed && "justify-center px-0"
        )}
      >
        <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded bg-[#22c55e] text-[10px] font-bold text-white">
          {initial}
        </div>
        {!isCollapsed && (
          <>
            <span className="min-w-0 flex-1 truncate text-[12px] font-medium leading-none text-white">
              {label}
            </span>
            <ChevronDown className={cn(
              "h-3.5 w-3.5 flex-shrink-0 text-[var(--text-muted)] transition-transform group-hover:text-white",
              open && "rotate-180"
            )} />
          </>
        )}
      </button>
      {open && !isCollapsed && (
        <div className="absolute left-[9px] right-2.5 top-0 z-50 overflow-hidden rounded-[10px] border border-[var(--border-default)] bg-[var(--surface-1)] shadow-2xl">
          <button
            onClick={() => setOpen(false)}
            className="flex w-full items-center gap-2.5 px-2.5 py-2.5 text-left hover:bg-[var(--surface-2)]"
          >
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-[7px] bg-[#22c55e] text-[13px] font-bold text-white">
              {initial}
            </div>
            <span className="min-w-0 flex-1 truncate text-[13px] font-semibold text-white">
              {label}
            </span>
          </button>

          <div className="space-y-1 px-2 pb-2.5">
          {workspaces.map(workspace => (
            <button
              key={workspace.id}
              onClick={() => {
                if (workspace.id === currentWorkspaceId) {
                  setOpen(false)
                  return
                }
                switchWorkspace(workspace)
                queryClient.invalidateQueries({ queryKey: workflowKeys.all })
                queryClient.invalidateQueries({ queryKey: folderKeys.all })
                if (location.pathname.startsWith('/workflows/')) {
                  navigate('/workflows')
                }
                setOpen(false)
              }}
              className={cn(
                "flex h-8 w-full items-center rounded-md px-2 text-left text-[12px] font-semibold transition-colors",
                workspace.id === currentWorkspaceId
                  ? "bg-[var(--surface-2)] text-white"
                  : "text-[var(--text-muted)] hover:bg-[var(--surface-2)] hover:text-white"
              )}
            >
              <span className="flex-1 truncate">{workspace.name}</span>
            </button>
          ))}
            <button
              onClick={handleCreateWorkspace}
              className="flex h-7 w-full items-center gap-2 rounded-md px-2 text-left text-[12px] font-semibold text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-2)] hover:text-white"
            >
              <Plus className="h-3.5 w-3.5" />
              Create new workspace
            </button>
          </div>

          <button
            onClick={() => {
              setOpen(false)
              navigate('/settings/team')
            }}
            className="flex h-10 w-full items-center gap-2.5 border-t border-[var(--border-default)] px-4 text-left text-[12px] font-semibold text-white transition-colors hover:bg-[var(--surface-2)]"
          >
            <UserPlus className="h-4 w-4 text-[var(--text-muted)]" />
            Invite members
          </button>
        </div>
      )}
    </div>
  )
}

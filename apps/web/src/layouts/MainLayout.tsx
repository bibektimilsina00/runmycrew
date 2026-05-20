import React from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from '@/components/navigation/sidebar'
import { CommandPalette } from '@/components/navigation/CommandPalette'
import { useWorkspaces } from '@/features/workspaces/hooks'
import { useMe } from '@/hooks/auth/use-auth'
import { useWorkspaceStore } from '@/stores/workspace-store'

export const MainLayout: React.FC = () => {
  useMe()
  const { isLoading } = useWorkspaces()
  const currentWorkspaceId = useWorkspaceStore(s => s.currentWorkspaceId)

  // After workspaces loaded but none found — show recovery UI
  // (shouldn't happen in normal flow; register always creates a personal workspace)
  if (!isLoading && !currentWorkspaceId) {
    return (
      <div className="flex h-screen items-center justify-center bg-[var(--bg)]">
        <div className="text-center space-y-3 max-w-sm px-6">
          <p className="text-[16px] font-semibold text-white">No workspace found</p>
          <p className="text-[13px] text-[var(--text-muted)]">
            Your workspace could not be loaded. Try reloading the page.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 rounded-lg bg-white px-4 py-2 text-[13px] font-medium text-black hover:bg-gray-100 transition-colors"
          >
            Reload
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-[var(--surface-1)]">
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="flex-1 flex flex-col bg-[var(--surface-1)] p-[8px] pl-0">
          <div className="flex-1 overflow-hidden rounded-[8px] border border-[var(--border-default)] bg-[var(--bg)] relative shadow-sm">
            <Outlet />
          </div>
        </main>
      </div>
      <CommandPalette />
    </div>
  )
}

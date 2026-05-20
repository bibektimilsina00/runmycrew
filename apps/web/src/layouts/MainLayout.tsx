import React from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from '@/components/navigation/sidebar'
import { CommandPalette } from '@/components/navigation/CommandPalette'
import { useWorkspaces } from '@/features/workspaces/hooks'
import { useMe } from '@/hooks/auth/use-auth'

export const MainLayout: React.FC = () => {
  // Fetch user profile on mount
  useMe()
  useWorkspaces()

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-[var(--surface-1)]">
      <div className="flex min-h-0 flex-1">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Canvas (bg) */}
        <main className="flex-1 flex flex-col bg-[var(--surface-1)] p-[8px] pl-0">
          <div className="flex-1 overflow-hidden rounded-[8px] border border-[var(--border-default)] bg-[var(--bg)] relative shadow-sm">
            <Outlet />
          </div>
        </main>
      </div>
      
      {/* Global Search Overlay */}
      <CommandPalette />
    </div>
  )
}

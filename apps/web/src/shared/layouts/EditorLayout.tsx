import { Outlet } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { AppOverlays } from './app-layout/app-overlays'
import { AppSidebar } from './app-layout/app-sidebar'
import { WorkflowDialogs } from './app-layout/workflow-dialogs'
import { useAppLayoutController } from './app-layout/use-app-layout-controller'

export function EditorLayout() {
  const controller = useAppLayoutController()

  return (
    <div
      className={cn(
        'group/shell relative h-screen grid grid-cols-[244px_1fr] z-10',
        'data-[collapsed=true]:grid-cols-[64px_1fr]',
      )}
      data-collapsed={controller.collapsed}
    >
      <div className="dot-grid" />

      <AppSidebar controller={controller} />

      <div className="relative flex h-screen min-h-0 flex-col overflow-hidden">
        <Outlet />
      </div>

      <AppOverlays controller={controller} />
      <WorkflowDialogs controller={controller} />
    </div>
  )
}

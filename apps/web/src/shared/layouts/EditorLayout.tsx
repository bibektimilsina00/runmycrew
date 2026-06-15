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
        'group/shell relative h-screen grid grid-cols-[244px_1fr] z-10 transition-[grid-template-columns] duration-300 ease-in-out',
        'data-[collapsed=true]:grid-cols-[80px_1fr]',
      )}
      data-collapsed={controller.collapsed}
    >
      <AppSidebar controller={controller} variant="floating" />

      <div className="relative flex h-[calc(100vh-28px)] my-[14px] mr-[14px] ml-0 min-h-0 flex-col overflow-hidden bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)]">
        <Outlet context={controller} />
      </div>

      <AppOverlays controller={controller} />
      <WorkflowDialogs controller={controller} />
    </div>
  )
}

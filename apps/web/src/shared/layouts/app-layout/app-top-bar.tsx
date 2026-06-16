import type { AppLayoutController } from './use-app-layout-controller'
import { AppTopBarActions } from './app-top-bar-actions'

interface AppTopBarProps {
  controller: AppLayoutController
}

export function AppTopBar({ controller }: AppTopBarProps) {
  const { currentWorkspace, pageLabel, selectedTableName } = controller

  return (
    <header className="flex items-center justify-between py-[8px] px-[22px] border-b border-[var(--border-faint)] bg-[var(--bg-2)] shrink-0">
      <div className="flex items-center gap-[8px] text-[13px] text-[var(--text-mute)]">
        <span>{currentWorkspace?.name ?? 'My workspace'}</span>
        <span className="text-[var(--text-dim)]">/</span>
        {selectedTableName ? (
          <>
            <span className="text-[var(--text-mute)]">{pageLabel}</span>
            <span className="text-[var(--text-dim)]">/</span>
            <span className="text-[var(--text)] font-medium">{selectedTableName}</span>
          </>
        ) : (
          <span className="text-[var(--text)] font-medium">{pageLabel}</span>
        )}
      </div>

      <AppTopBarActions controller={controller} />
    </header>
  )
}

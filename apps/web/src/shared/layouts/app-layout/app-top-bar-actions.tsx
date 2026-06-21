import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { AppLayoutController } from './use-app-layout-controller'
import { MENU_ITEM_CLASS } from './navigation'

interface AppTopBarActionsProps {
  controller: AppLayoutController
}

export function AppTopBarActions({ controller }: AppTopBarActionsProps) {
  const {
    user,
    logout,
    theme,
    toggleTheme,
    profileOpen,
    setProfileOpen,
    setShortcutsOpen,
    setFeedbackOpen,
  } = controller

  const userInitial = (user?.full_name || user?.email || '?').slice(0, 1).toUpperCase()

  return (
    <div className="flex items-center gap-[6px]">
      <button className="w-[32px] h-[32px] inline-flex items-center justify-center rounded-[8px] text-[var(--text-mute)] relative transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[16px] [&_svg]:h-[16px]" title="Activity"><Icons.Activity /></button>
      <button className="w-[32px] h-[32px] inline-flex items-center justify-center rounded-[8px] text-[var(--text-mute)] relative transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[16px] [&_svg]:h-[16px]" title="Keyboard shortcuts" onClick={() => setShortcutsOpen(true)}><Icons.Cmd /></button>

      <div className="relative">
        <button
          className={cn(
            'w-[28px] h-[28px] rounded-[8px] cursor-pointer inline-flex items-center justify-center text-[11px] font-semibold tracking-tight bg-cover bg-center transition-[filter,opacity] duration-120',
            // Two distinct treatments: avatar URL → bare image disc, no
            // bg / border / text. No avatar → solid accent chip with
            // initial — same pattern as the workspace-selector chips so
            // the brand reads consistently across the chrome.
            user?.avatar_url
              ? 'hover:brightness-110'
              : 'bg-[var(--accent)] text-white hover:brightness-110',
          )}
          onClick={() => setProfileOpen(value => !value)}
          aria-label="Account"
          style={{ backgroundImage: user?.avatar_url ? `url(${user.avatar_url})` : undefined }}
        >
          {!user?.avatar_url && userInitial}
        </button>

        {profileOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setProfileOpen(false)} />
            <div className="absolute top-[calc(100%+8px)] right-0 w-[260px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[6px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] z-50 animate-in fade-in slide-in-from-top-2">
              <div className="flex items-center gap-[10px] pt-[8px] px-[8px] pb-[10px]">
                <span
                  className={cn(
                    'w-[32px] h-[32px] rounded-[9px] inline-flex items-center justify-center text-[13px] font-semibold shrink-0 bg-cover bg-center',
                    user?.avatar_url ? '' : 'bg-[var(--accent)] text-white',
                  )}
                  style={{ backgroundImage: user?.avatar_url ? `url(${user.avatar_url})` : undefined }}
                >
                  {!user?.avatar_url && userInitial}
                </span>
                <span className="flex flex-col gap-[1px] min-w-0">
                  <span className="text-[13px] font-medium">{user?.full_name || 'Anonymous'}</span>
                  <span className="text-[11px] text-[var(--text-faint)] font-mono">{user?.email}</span>
                </span>
              </div>

              <NavLink to={APP_ROUTES.SETTINGS} className={MENU_ITEM_CLASS} onClick={() => setProfileOpen(false)}>
                <Icons.Settings /> Account settings <span className="kbd">⌘,</span>
              </NavLink>
              <NavLink to={APP_ROUTES.WORKSPACE_SETTINGS} className={MENU_ITEM_CLASS} onClick={() => setProfileOpen(false)}>
                <Icons.Settings /> Workspace settings
              </NavLink>
              <NavLink to={APP_ROUTES.CONNECTIONS} className={MENU_ITEM_CLASS} onClick={() => setProfileOpen(false)}>
                <Icons.Plug /> Connected apps
              </NavLink>
              <NavLink to={APP_ROUTES.RUNS} className={MENU_ITEM_CLASS} onClick={() => setProfileOpen(false)}>
                <Icons.Activity /> Run usage
              </NavLink>
              <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
              <button className={MENU_ITEM_CLASS} onClick={toggleTheme}>
                <Icons.Moon /> Appearance
                <span className="ml-auto font-mono text-[10.5px] text-[var(--text-faint)] capitalize">{theme}</span>
              </button>
              <button className={MENU_ITEM_CLASS} onClick={() => { setProfileOpen(false); setShortcutsOpen(true) }}>
                <Icons.Cmd /> Keyboard shortcuts <span className="ml-auto kbd">?</span>
              </button>
              <button className={MENU_ITEM_CLASS} onClick={() => { setProfileOpen(false); window.open('https://runmycrew.com/docs', '_blank', 'noopener') }}>
                <Icons.Doc /> Documentation
              </button>
              <button className={MENU_ITEM_CLASS} onClick={() => { setProfileOpen(false); setFeedbackOpen(true) }}>
                <Icons.Feedback /> Send feedback
              </button>
              <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
              <button className={cn(MENU_ITEM_CLASS, 'text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.10)]')} onClick={() => { setProfileOpen(false); logout() }}>
                <Icons.SignOut /> Sign out
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

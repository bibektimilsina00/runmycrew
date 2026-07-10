import React from 'react'
import { createPortal } from 'react-dom'
import { useNavigate, useLocation } from 'react-router-dom'
import { Icons } from '@/shared/components/icons'
import { cn } from '@/lib/cn'
import { APP_ROUTES } from '@/shared/constants/routes'
import type { Loop } from '../types/loopsTypes'

const ROW_BASE =
  'group/crew flex items-center gap-[10px] py-[6px] px-[10px] rounded-[8px] text-[13px] font-medium w-full cursor-pointer transition-colors duration-100 hover:bg-[var(--surface)] relative'

const MENU_BTN =
  'w-[22px] h-[22px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center opacity-0 transition-all duration-100 shrink-0 hover:bg-[var(--surface-2)] hover:text-[var(--text)] group-hover/crew:opacity-100 [&_svg]:w-[13px] [&_svg]:h-[13px]'

const MENU_ITEM =
  'flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0'

interface SidebarCrewItemProps {
  crew: Loop
  onRename: (id: string, name: string) => void
  onDelete: (id: string, name: string) => void
  onDuplicate: (id: string) => void
  onToggleActive: (id: string) => void
  openMenuId: string | null
  setOpenMenuId: (id: string | null) => void
}

export function SidebarCrewItem({
  crew,
  onRename,
  onDelete,
  onDuplicate,
  onToggleActive,
  openMenuId,
  setOpenMenuId,
}: SidebarCrewItemProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const isActiveRoute = location.pathname === APP_ROUTES.CREW_EDITOR(crew.id)

  const isMenuOpen = openMenuId === crew.id
  const [menuPos, setMenuPos] = React.useState<{ top: number; left: number } | null>(null)

  const openMenu = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    if (isMenuOpen) {
      setOpenMenuId(null)
      return
    }
    const rect = e.currentTarget.getBoundingClientRect()
    setMenuPos({ top: rect.bottom + 4, left: rect.left })
    setOpenMenuId(crew.id)
  }

  const closeMenu = () => setOpenMenuId(null)

  const color = crew.color ?? '#8b5cf6'

  return (
    <div
      className={cn(
        ROW_BASE,
        isActiveRoute && 'bg-[var(--surface)] text-[var(--text)]',
        !isActiveRoute && 'text-[var(--text-mute)]',
      )}
      onClick={() => navigate(APP_ROUTES.CREW_EDITOR(crew.id))}
      title={crew.name}
    >
      <span
        className={cn(
          'h-[7px] w-[7px] shrink-0 rounded-full',
          crew.is_active ? 'animate-pulse' : 'opacity-70',
        )}
        style={{
          background: crew.is_active
            ? 'var(--ok, #10b981)'
            : color,
        }}
      />
      <span className="min-w-0 flex-1 truncate">{crew.name || 'Untitled crew'}</span>
      <button
        onClick={openMenu}
        className={MENU_BTN}
        title="Options"
        aria-label="Crew options"
      >
        <Icons.More />
      </button>

      {isMenuOpen && menuPos && createPortal(
        <>
          <div className="fixed inset-0 z-[9998]" onClick={closeMenu} />
          <div
            className="fixed z-[9999] flex w-[190px] flex-col gap-[2px] rounded-[11px] border border-[var(--border)] bg-[var(--bg-2)] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in slide-in-from-top-2 duration-100"
            style={{ top: menuPos.top, left: menuPos.left }}
          >
            <button
              className={MENU_ITEM}
              onClick={(e) => {
                e.stopPropagation()
                closeMenu()
                onToggleActive(crew.id)
              }}
            >
              {crew.is_active ? <Icons.Pause /> : <Icons.Play />}
              {crew.is_active ? 'Pause crew' : 'Activate crew'}
            </button>
            <button
              className={MENU_ITEM}
              onClick={(e) => {
                e.stopPropagation()
                closeMenu()
                const next = window.prompt('Rename crew', crew.name)
                if (next && next.trim() && next !== crew.name) onRename(crew.id, next.trim())
              }}
            >
              <Icons.Edit /> Rename
            </button>
            <button
              className={MENU_ITEM}
              onClick={(e) => {
                e.stopPropagation()
                closeMenu()
                onDuplicate(crew.id)
              }}
            >
              <Icons.Copy /> Duplicate
            </button>
            <div className="my-[4px] h-[1px] bg-[var(--border-faint)]" />
            <button
              className={cn(MENU_ITEM, 'text-[var(--err)] hover:bg-[var(--badge-err-bg)]')}
              onClick={(e) => {
                e.stopPropagation()
                closeMenu()
                onDelete(crew.id, crew.name)
              }}
            >
              <Icons.Trash /> Delete
            </button>
          </div>
        </>,
        document.body,
      )}
    </div>
  )
}

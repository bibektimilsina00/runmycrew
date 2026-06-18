'use client'

import Link from 'next/link'
import { useRef, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { EXTERNAL_LINKS } from '@/shared/constants/routes'
import { NAV_LINKS, type NavMenuKey } from '../data/site'
import { FuseMark } from './FuseMark'
import { NavMenu } from './NavMenu'

/**
 * Sticky top nav with mega-menu popups for Docs + Blog.
 *
 * Hover semantics:
 *   - mouseEnter on trigger → open after 80ms (debounced so flicking
 *     past the link doesn't pop the menu).
 *   - mouseLeave on trigger OR menu → close after 140ms (lets the
 *     cursor cross the small gap between the link and the menu shell).
 *   - mouseEnter back on either cancels the close timer.
 */
export function MarketingNav() {
  const [openMenu, setOpenMenu] = useState<NavMenuKey | null>(null)
  const openTimer  = useRef<ReturnType<typeof setTimeout> | null>(null)
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const cancel = (t: typeof openTimer) => {
    if (t.current) { clearTimeout(t.current); t.current = null }
  }

  const requestOpen = (menu: NavMenuKey) => {
    cancel(closeTimer)
    cancel(openTimer)
    openTimer.current = setTimeout(() => setOpenMenu(menu), 80)
  }
  const requestClose = () => {
    cancel(openTimer)
    cancel(closeTimer)
    closeTimer.current = setTimeout(() => setOpenMenu(null), 140)
  }
  const keepOpen = () => {
    cancel(closeTimer)
  }

  return (
    <header className="sticky top-0 z-40 backdrop-blur-xl supports-[backdrop-filter]:bg-background/65">
      <nav className="mx-auto flex h-16 max-w-[1280px] items-center gap-8 px-7">
        <Link href="/" className="flex shrink-0 items-center gap-[9px]">
          <FuseMark className="h-[28px] w-[28px] text-primary" />
          <span className="text-[19px] font-semibold tracking-[-0.03em] text-foreground">
            Fuse
          </span>
        </Link>

        <div className="ml-auto hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((item) => {
            const isOpen = item.menu && openMenu === item.menu
            return (
              <div
                key={item.label}
                className="relative"
                onMouseEnter={item.menu ? () => requestOpen(item.menu!) : undefined}
                onMouseLeave={item.menu ? requestClose : undefined}
              >
                <Link
                  href={item.href}
                  className={`group inline-flex items-center gap-1 rounded-md px-3 py-2 text-[15px] font-medium transition-colors ${
                    isOpen ? 'text-foreground' : 'text-foreground/90 hover:text-foreground'
                  }`}
                >
                  {item.label}
                  {item.menu && (
                    <ChevronDown
                      className={`h-[14px] w-[14px] text-foreground/55 transition-transform ${
                        isOpen ? 'rotate-180' : 'group-hover:translate-y-px'
                      }`}
                      strokeWidth={2}
                    />
                  )}
                </Link>

                {isOpen && item.menu && (
                  // Fixed + horizontally centered on the viewport so the
                  // 720px shell never bleeds off-screen regardless of
                  // which trigger opened it. Top sits just under the
                  // 64px nav with an 8px gap.
                  <div className="fixed left-1/2 top-[64px] z-50 -translate-x-1/2 pt-2">
                    <NavMenu
                      which={item.menu}
                      onMouseEnter={keepOpen}
                      onMouseLeave={requestClose}
                    />
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <div className="flex shrink-0 items-center">
          <Link
            href={EXTERNAL_LINKS.PRODUCT}
            className="inline-flex h-[30px] items-center gap-[7px] rounded-[8px] bg-primary px-[14px] text-[13px] font-semibold text-primary-foreground transition-[filter] hover:brightness-110"
          >
            Go to app
          </Link>
        </div>
      </nav>
    </header>
  )
}

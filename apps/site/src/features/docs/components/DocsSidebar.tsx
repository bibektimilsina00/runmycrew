'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { NavGroup } from '../source'

/**
 * Left rail for `/docs/*`. Groups render as uppercase section headers with a
 * flat leaf list beneath — the tree is short enough that accordioning it just
 * hides structure users scan. Active leaf gets the accent rail + foreground.
 */
export function DocsSidebar({ nav }: { nav: NavGroup[] }) {
  const path = usePathname()

  return (
    <nav className="flex h-full flex-col gap-6 overflow-y-auto py-8 pr-5 [scrollbar-width:thin] [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-white/10">
      {nav.map((group) => (
        <div key={group.group} className="flex flex-col gap-0.5">
          <div className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/60">
            {group.group}
          </div>
          {group.items.map((leaf) => {
            const active = path === leaf.href
            return (
              <Link
                key={leaf.href}
                href={leaf.href}
                className={`relative rounded-md px-3 py-[7px] text-[13.5px] transition-colors ${
                  active
                    ? 'bg-white/[0.05] font-medium text-foreground'
                    : 'text-muted-foreground/80 hover:bg-white/[0.025] hover:text-foreground'
                }`}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 h-4 w-[2px] -translate-y-1/2 rounded-r-full bg-primary" />
                )}
                {leaf.frontmatter.title}
              </Link>
            )
          })}
        </div>
      ))}
    </nav>
  )
}

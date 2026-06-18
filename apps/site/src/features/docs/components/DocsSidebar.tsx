'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { DOCS_NAV } from '../data/nav'

/**
 * Left rail for `/docs/*`. Plain group→leaf tree, no collapsibles for
 * v1 — the list is short and accordioning it just hides structure
 * users scan visually. Active leaf gets the accent rail + foreground.
 */
export function DocsSidebar() {
  const path = usePathname()

  return (
    <nav className="flex h-full flex-col gap-7 overflow-y-auto py-8 pr-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {DOCS_NAV.map((group) => (
        <div key={group.group} className="flex flex-col gap-1.5">
          <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
            {group.group}
          </div>
          {group.items.map((leaf) => {
            const href = leaf.slug ? `/docs/${leaf.slug}` : '/docs'
            const active = path === href
            return (
              <Link
                key={leaf.slug}
                href={href}
                className={`relative rounded-md px-3 py-1.5 text-[13.5px] transition-colors ${
                  active
                    ? 'bg-white/[0.04] font-medium text-foreground'
                    : 'text-muted-foreground/85 hover:bg-white/[0.025] hover:text-foreground'
                }`}
              >
                {active && (
                  <span className="absolute left-0 top-1/2 h-4 w-[2px] -translate-y-1/2 rounded-r-full bg-primary" />
                )}
                {leaf.title}
              </Link>
            )
          })}
        </div>
      ))}
    </nav>
  )
}

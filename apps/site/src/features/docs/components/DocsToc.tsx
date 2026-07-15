'use client'

import { useEffect, useState } from 'react'
import type { TocEntry } from '../source'

/**
 * Right rail "On this page" outline with scroll-spy. An IntersectionObserver
 * tracks which heading is in view and highlights the matching entry. Headings
 * and their ids come from the source loader (github-slugger), so anchors line
 * up with rehype-slug's output.
 */
export function DocsToc({ items }: { items: TocEntry[] }) {
  const [active, setActive] = useState<string | null>(null)

  useEffect(() => {
    if (items.length === 0) return
    const headings = items
      .map((it) => document.getElementById(it.id))
      .filter((el): el is HTMLElement => el !== null)

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (visible[0]) setActive(visible[0].target.id)
      },
      { rootMargin: '-88px 0px -70% 0px', threshold: [0, 1] },
    )
    headings.forEach((h) => observer.observe(h))
    return () => observer.disconnect()
  }, [items])

  if (items.length === 0) return null

  return (
    <aside className="sticky top-[64px] flex max-h-[calc(100vh-64px)] flex-col gap-3 overflow-y-auto py-14 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/60">
        On this page
      </div>
      <div className="flex flex-col gap-0.5 border-l border-border">
        {items.map((it) => (
          <a
            key={it.id}
            href={`#${it.id}`}
            className={`-ml-px border-l py-1 text-[12.5px] leading-snug transition-colors ${
              it.depth === 3 ? 'pl-6' : 'pl-3'
            } ${
              active === it.id
                ? 'border-primary font-medium text-foreground'
                : 'border-transparent text-muted-foreground/75 hover:border-foreground/40 hover:text-foreground'
            }`}
          >
            {it.label}
          </a>
        ))}
      </div>
    </aside>
  )
}

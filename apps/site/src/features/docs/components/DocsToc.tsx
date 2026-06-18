import Link from 'next/link'

export type TocEntry = { id: string; label: string; depth?: 2 | 3 }

/**
 * Right rail "On this page" outline. Statically driven for now —
 * future MDX integration can produce this from heading nodes during
 * compile. Depth controls indentation (h2 vs h3).
 */
export function DocsToc({ items }: { items: TocEntry[] }) {
  if (items.length === 0) return null
  return (
    <aside className="sticky top-[88px] flex flex-col gap-3 py-8">
      <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
        On this page
      </div>
      <div className="flex flex-col gap-1.5 border-l border-border">
        {items.map((it) => (
          <Link
            key={it.id}
            href={`#${it.id}`}
            className={`-ml-px border-l border-transparent pl-3 text-[12.5px] text-muted-foreground/85 transition-colors hover:border-foreground/60 hover:text-foreground ${
              it.depth === 3 ? 'pl-6' : ''
            }`}
          >
            {it.label}
          </Link>
        ))}
      </div>
    </aside>
  )
}

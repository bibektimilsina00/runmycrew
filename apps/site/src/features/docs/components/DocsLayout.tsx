import type { ReactNode } from 'react'
import { DocsSidebar } from './DocsSidebar'

/**
 * Three-column docs shell: left sidebar (240px), center prose (max ~720),
 * right TOC slot (220px) — Vercel-style. Below `lg` the sidebar drops
 * off and the page becomes single-column for mobile reading.
 */
export function DocsLayout({
  children,
  toc,
}: {
  children: ReactNode
  toc?: ReactNode
}) {
  return (
    <div className="mx-auto grid w-full max-w-[1280px] grid-cols-1 px-6 lg:grid-cols-[240px_minmax(0,1fr)_220px] lg:gap-x-10 lg:px-8">
      <aside className="hidden lg:block">
        <div className="sticky top-[64px] h-[calc(100vh-64px)]">
          <DocsSidebar />
        </div>
      </aside>
      <main className="min-w-0 py-12 lg:py-16">
        <article className="prose-docs">{children}</article>
      </main>
      <div className="hidden lg:block">{toc}</div>
    </div>
  )
}

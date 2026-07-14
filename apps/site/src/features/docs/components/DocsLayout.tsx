import type { ReactNode } from 'react'
import Link from 'next/link'
import { ChevronRight, ArrowLeft, ArrowRight } from 'lucide-react'
import { getNav, type LoadedDoc } from '../source'
import { DocsSidebar } from './DocsSidebar'
import { DocsToc } from './DocsToc'
import { CopyPageButton } from './CopyPageButton'

/**
 * Three-column docs shell: left sidebar (nav from the filesystem source),
 * center prose, right "On this page" TOC. Header shows the group breadcrumb +
 * copy-page; footer shows prev/next pagination. Below `lg` it collapses to a
 * single reading column.
 */
export function DocsLayout({ doc, children }: { doc: LoadedDoc; children: ReactNode }) {
  const nav = getNav()
  const { frontmatter } = doc.meta

  return (
    <div className="mx-auto grid w-full max-w-[1400px] grid-cols-1 px-6 lg:grid-cols-[248px_minmax(0,1fr)_212px] lg:gap-x-12 lg:px-8">
      <aside className="hidden lg:block">
        <div className="sticky top-[64px] h-[calc(100vh-64px)]">
          <DocsSidebar nav={nav} />
        </div>
      </aside>

      <main className="min-w-0 py-10 lg:py-14">
        {/* Breadcrumb + copy page */}
        <div className="mb-7 flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5 text-[12.5px] text-muted-foreground/70">
            <span>{frontmatter.group}</span>
            <ChevronRight className="h-3.5 w-3.5" />
            <span className="text-foreground/80">{frontmatter.title}</span>
          </div>
          <CopyPageButton />
        </div>

        <article className="prose-docs">
          <h1>{frontmatter.title}</h1>
          {frontmatter.description && <p className="lead">{frontmatter.description}</p>}
          {children}
        </article>

        <DocsPager prev={doc.prev} next={doc.next} />
      </main>

      <div className="hidden lg:block">
        <DocsToc items={doc.toc} />
      </div>
    </div>
  )
}

function DocsPager({
  prev,
  next,
}: {
  prev: LoadedDoc['prev']
  next: LoadedDoc['next']
}) {
  if (!prev && !next) return null
  return (
    <nav className="mt-16 grid grid-cols-2 gap-4 border-t border-border pt-8">
      {prev ? (
        <Link
          href={prev.href}
          className="group flex flex-col gap-1 rounded-[12px] border border-border bg-card/20 px-4 py-3 no-underline transition-colors hover:border-primary/40 hover:bg-card/50"
        >
          <span className="flex items-center gap-1.5 text-[12px] text-muted-foreground/70">
            <ArrowLeft className="h-3.5 w-3.5" /> Previous
          </span>
          <span className="text-[14px] font-medium text-foreground">{prev.frontmatter.title}</span>
        </Link>
      ) : (
        <span />
      )}
      {next ? (
        <Link
          href={next.href}
          className="group flex flex-col items-end gap-1 rounded-[12px] border border-border bg-card/20 px-4 py-3 text-right no-underline transition-colors hover:border-primary/40 hover:bg-card/50"
        >
          <span className="flex items-center gap-1.5 text-[12px] text-muted-foreground/70">
            Next <ArrowRight className="h-3.5 w-3.5" />
          </span>
          <span className="text-[14px] font-medium text-foreground">{next.frontmatter.title}</span>
        </Link>
      ) : (
        <span />
      )}
    </nav>
  )
}

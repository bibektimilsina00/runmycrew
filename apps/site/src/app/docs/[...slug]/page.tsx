import { notFound } from 'next/navigation'
import { MarketingNav } from '@/features/marketing'
import { DocsLayout, DocsToc, findDoc, type TocEntry } from '@/features/docs'

/**
 * Catch-all docs route. For now every page renders a placeholder body
 * derived from the leaf's `intro`. Swap this file to MDX (Fumadocs /
 * next-mdx-remote) when content arrives — the URL + layout shape stay
 * identical so links don't churn.
 */
export default async function DocPage({
  params,
}: {
  params: Promise<{ slug: string[] }>
}) {
  const { slug } = await params
  const match = findDoc(slug)
  if (!match) notFound()

  const { group, leaf } = match
  const toc: TocEntry[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'usage',    label: 'Usage' },
  ]

  return (
    <>
      <MarketingNav />
      <DocsLayout toc={<DocsToc items={toc} />}>
        <p className="text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
          {group}
        </p>
        <h1>{leaf.title}</h1>
        {leaf.intro && <p className="lead">{leaf.intro}</p>}

        <h2 id="overview">Overview</h2>
        <p>
          This page is a placeholder. Content for <strong>{leaf.title}</strong>{' '}
          is being written and will land in a future release.
        </p>

        <h2 id="usage">Usage</h2>
        <p>Until then, use the sidebar to explore other sections.</p>
      </DocsLayout>
    </>
  )
}

import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { MarketingNav } from '@/features/marketing'
import { DocsLayout, DocsToc, findDoc, DOC_CONTENT, type TocEntry } from '@/features/docs'

/**
 * Catch-all docs route. Renders rich content from `DOC_CONTENT` when the
 * slug has a body; otherwise falls back to a short placeholder derived from
 * the nav leaf. The URL + layout shape stay identical either way.
 */

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string[] }>
}): Promise<Metadata> {
  const { slug } = await params
  const match = findDoc(slug)
  if (!match) return { title: 'Docs' }
  return {
    title: `${match.leaf.title} · Docs`,
    description: match.leaf.intro,
  }
}

export default async function DocPage({
  params,
}: {
  params: Promise<{ slug: string[] }>
}) {
  const { slug } = await params
  const match = findDoc(slug)
  if (!match) notFound()

  const { group, leaf } = match
  const content = DOC_CONTENT[slug.join('/')]

  // Rich content path.
  if (content) {
    return (
      <>
        <MarketingNav />
        <DocsLayout toc={<DocsToc items={content.toc} />}>
          {content.body}
        </DocsLayout>
      </>
    )
  }

  // Placeholder fallback for any leaf without a body yet.
  const toc: TocEntry[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'usage', label: 'Usage' },
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
          This page is being written. Use the sidebar to explore the rest of
          the docs in the meantime.
        </p>
        <h2 id="usage">Usage</h2>
        <p>Check back soon.</p>
      </DocsLayout>
    </>
  )
}

import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { MarketingNav } from '@/features/marketing'
import { DocsLayout } from '@/features/docs'
import { getAllSlugs, getDoc } from '@/features/docs/source'
import { DocBody } from '@/features/docs/components/DocBody'

/**
 * Catch-all docs route. Content lives in `src/content/docs/**.mdx`; this
 * reads the file for the slug, compiles the MDX on the server, and renders
 * it inside the shared docs shell. Fully static — every slug is prerendered
 * from `generateStaticParams`.
 */

export const dynamicParams = false

export function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }))
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string[] }>
}): Promise<Metadata> {
  const { slug } = await params
  const doc = getDoc(slug)
  if (!doc) return { title: 'Docs' }
  return {
    title: `${doc.meta.frontmatter.title} · RunMyCrew Docs`,
    description: doc.meta.frontmatter.description,
  }
}

export default async function DocPage({
  params,
}: {
  params: Promise<{ slug: string[] }>
}) {
  const { slug } = await params
  const doc = getDoc(slug)
  if (!doc) notFound()

  return (
    <>
      <MarketingNav />
      <DocsLayout doc={doc}>
        <DocBody source={doc.content} />
      </DocsLayout>
    </>
  )
}

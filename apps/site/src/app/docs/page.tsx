import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { MarketingNav } from '@/features/marketing'
import { DocsLayout } from '@/features/docs'
import { getDoc } from '@/features/docs/source'
import { DocBody } from '@/features/docs/components/DocBody'

/** Docs home — renders `src/content/docs/index.mdx` through the shared shell. */
export function generateMetadata(): Metadata {
  const doc = getDoc([])
  return {
    title: `${doc?.meta.frontmatter.title ?? 'Docs'} · RunMyCrew Docs`,
    description: doc?.meta.frontmatter.description,
  }
}

export default async function DocsHome() {
  const doc = getDoc([])
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

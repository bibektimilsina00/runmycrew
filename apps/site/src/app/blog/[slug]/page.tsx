import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'
import { PostVisual, findPost, POSTS } from '@/features/blog'

/**
 * Single blog post. Hero meta + cover above the prose body. Bottom
 * shows related posts (3 most-recent excluding the current).
 */
export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const post = findPost(slug)
  if (!post) notFound()

  const related = POSTS.filter((p) => p.slug !== post.slug).slice(0, 3)

  return (
    <>
      <MarketingNav />
      <main>
        <article>
          <section className="pt-[120px] sm:pt-[160px]">
            <Container className="max-w-[820px] px-7">
              <Link
                href="/blog"
                className="mb-7 inline-flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                <ArrowLeft className="h-[14px] w-[14px]" strokeWidth={1.9} /> Back to blog
              </Link>

              <div className="flex items-center gap-2 text-[11.5px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
                <span className="text-primary">{post.category}</span>
                <span className="text-border">·</span>
                <span>{post.date}</span>
                <span className="text-border">·</span>
                <span>{post.read}</span>
              </div>
              <h1 className="m-0 mt-4 text-balance text-[clamp(34px,4.4vw,52px)] font-[560] leading-[1.08] tracking-[-0.022em] text-foreground">
                {post.title}
              </h1>
              <p className="m-0 mt-4 text-[17px] leading-[1.55] text-muted-foreground">
                {post.excerpt}
              </p>
            </Container>
          </section>

          <section className="mt-12">
            <Container className="max-w-[1080px] px-7">
              <div className="aspect-[16/9] overflow-hidden rounded-[14px] border border-border">
                <PostVisual which={post.visual} />
              </div>
            </Container>
          </section>

          <section className="my-16">
            <Container className="max-w-[820px] px-7">
              <div className="prose-docs">
                <p className="lead">
                  This post is a placeholder. Real copy will land when the
                  content layer ships — for now the layout is the proof.
                </p>
                <h2>Why it matters</h2>
                <p>
                  Fuse is built so teams can ship integrations in an afternoon
                  instead of a sprint, and so AI agents can use the same
                  workflows humans do without translation cost.
                </p>
                <h2>Get started</h2>
                <p>
                  Spin up a workspace, connect an app, and describe what you
                  want to automate. Fuse AI does the rest.
                </p>
              </div>
            </Container>
          </section>
        </article>

        <section className="border-t border-border py-16">
          <Container className="max-w-[1280px] px-7">
            <h2 className="m-0 mb-8 text-[22px] font-semibold tracking-[-0.018em] text-foreground">
              More from the blog
            </h2>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {related.map((p) => (
                <Link
                  key={p.slug}
                  href={`/blog/${p.slug}`}
                  className="group block overflow-hidden rounded-[12px] border border-border bg-card/30 transition-colors hover:border-foreground/25 hover:bg-card"
                >
                  <div className="aspect-[16/10]">
                    <PostVisual which={p.visual} />
                  </div>
                  <div className="flex flex-col gap-2 p-5">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.07em] text-primary">
                      {p.category}
                    </div>
                    <h3 className="m-0 text-[16px] font-semibold leading-snug text-foreground">
                      {p.title}
                    </h3>
                  </div>
                </Link>
              ))}
            </div>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}

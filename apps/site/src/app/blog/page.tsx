import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'
import { BlogCard, featuredPost, otherPosts } from '@/features/blog'

/**
 * Blog index. Feature hero spans the full row, then a 3-up grid of the
 * remaining posts. Filters / category chips will land alongside MDX
 * when the content layer is in place.
 */
export default function BlogIndex() {
  const feature = featuredPost()
  const rest = otherPosts()

  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-10 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[1280px] px-7">
            <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
                  Blog
                </p>
                <h1 className="m-0 mt-3 text-[clamp(34px,4.4vw,56px)] font-[560] leading-[1.08] tracking-[-0.022em] text-foreground">
                  The Fuse blog
                </h1>
                <p className="m-0 mt-3 max-w-[600px] text-[15px] text-muted-foreground">
                  Product launches, engineering deep dives, and customer stories.
                </p>
              </div>
            </div>

            <BlogCard post={feature} variant="feature" />
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[1280px] px-7">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {rest.map((p) => (
                <BlogCard key={p.slug} post={p} />
              ))}
            </div>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}

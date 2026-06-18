import Link from 'next/link'
import type { BlogPost } from '../data/posts'
import { PostVisual } from './PostVisual'

interface Props {
  post: BlogPost
  variant?: 'default' | 'feature'
}

/**
 * Post card. Default = grid tile (cover above title + meta). Feature =
 * landscape hero used on the index hero row, wider cover with a bigger
 * headline. Borders + tints stay subtle so the cover does the work.
 */
export function BlogCard({ post, variant = 'default' }: Props) {
  const feature = variant === 'feature'
  return (
    <Link
      href={`/blog/${post.slug}`}
      className={`group block overflow-hidden rounded-[12px] border border-border bg-card/30 transition-colors hover:border-foreground/25 hover:bg-card ${
        feature ? 'lg:flex lg:flex-row' : ''
      }`}
    >
      <div className={feature ? 'aspect-[16/10] lg:aspect-auto lg:w-[55%]' : 'aspect-[16/10]'}>
        <PostVisual which={post.visual} />
      </div>
      <div className={`flex flex-col gap-3 p-5 ${feature ? 'lg:flex-1 lg:p-7' : ''}`}>
        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
          <span className="text-primary">{post.category}</span>
          <span className="text-border">·</span>
          <span>{post.date}</span>
          <span className="text-border">·</span>
          <span>{post.read}</span>
        </div>
        <h3
          className={`m-0 text-balance text-foreground tracking-[-0.018em] ${
            feature ? 'text-[clamp(22px,2.4vw,30px)] font-semibold leading-[1.2]' : 'text-[17px] font-semibold leading-snug'
          }`}
        >
          {post.title}
        </h3>
        <p className={`m-0 text-muted-foreground ${feature ? 'text-[15px] leading-[1.55]' : 'text-[13.5px] leading-[1.55]'}`}>
          {post.excerpt}
        </p>
      </div>
    </Link>
  )
}

/**
 * Static blog metadata. Bodies are stubbed via `excerpt` until MDX or
 * CMS content lands. Slugs are the URL segment under `/blog/<slug>`.
 */
export type BlogCategory = 'Product' | 'Engineering' | 'Company' | 'Customer story'

// PostVisual variants the blog cards/visual component support today. Extend
// PostVisual.tsx in lockstep when adding a new key here.

export type BlogPost = {
  slug: string
  title: string
  excerpt: string
  category: BlogCategory
  date: string         // ISO-ish, used as display string
  read: string         // e.g. '4 min read'
  visual: 'mothership' | 'series' | 'realtime' | 'executor' | 'enterprise' | 'crew-ai' | 'agent-loops'
  featured?: boolean
  body?: string        // optional stub markdown-ish body for the detail page
}

export const POSTS: BlogPost[] = [
  {
    slug: 'loop-engineering',
    title: 'Loop engineering — autonomous agents that run on their own',
    excerpt:
      'Agents that own recurring work — triaging bugs, merging Dependabot PRs, turning Sentry into GitHub issues — with hard budgets, escalation, and a live trace you can audit step by step.',
    category: 'Engineering',
    date: 'Jun 20, 2026',
    read: '9 min read',
    visual: 'agent-loops',
    featured: true,
  },
  {
    slug: 'introducing-crew-ai',
    title: 'Introducing Crew AI',
    excerpt: 'Generate entire branching workflows from a single sentence. Crew AI ships today on every plan.',
    category: 'Product',
    date: 'Jun 10, 2026',
    read: '5 min read',
    visual: 'crew-ai',
  },
  {
    slug: 'enterprise',
    title: 'Enterprise features for fast, scalable workflows',
    excerpt: 'SSO, audit logs, region pinning, and a private slack. Built for teams that need workflows their compliance team trusts.',
    category: 'Product',
    date: 'Jun 8, 2026',
    read: '6 min read',
    visual: 'enterprise',
  },
  {
    slug: 'seed-announcement',
    title: '$8M Seed round',
    excerpt: 'Standard, SV Angel and Sequoia lead our seed to build the automation system every team deserves.',
    category: 'Company',
    date: 'Jun 1, 2026',
    read: '3 min read',
    visual: 'series',
  },
  {
    slug: 'realtime-collaboration',
    title: 'Realtime collaboration',
    excerpt: 'Multiplayer cursors and live edits on the workflow canvas. Build with your team without leaving RunMyCrew.',
    category: 'Engineering',
    date: 'May 27, 2026',
    read: '7 min read',
    visual: 'realtime',
  },
  {
    slug: 'inside-the-executor',
    title: 'Inside the RunMyCrew executor',
    excerpt: 'How we run thousands of workflows per second with predictable latency and zero dropped runs.',
    category: 'Engineering',
    date: 'May 21, 2026',
    read: '12 min read',
    visual: 'executor',
  },
  {
    slug: 'mothership',
    title: 'Introducing Mothership',
    excerpt: 'A new way to deploy your RunMyCrew runtime across regions with one click.',
    category: 'Product',
    date: 'May 12, 2026',
    read: '4 min read',
    visual: 'mothership',
  },
]

export function findPost(slug: string): BlogPost | undefined {
  return POSTS.find((p) => p.slug === slug)
}

export function featuredPost(): BlogPost {
  return POSTS.find((p) => p.featured) ?? POSTS[0]
}

export function otherPosts(): BlogPost[] {
  const feat = featuredPost()
  return POSTS.filter((p) => p.slug !== feat.slug)
}

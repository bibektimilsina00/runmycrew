import type { MetadataRoute } from 'next'
import { MARKETING_URL } from '@/shared/constants/routes'
import { POSTS } from '@/features/blog/data/posts'
import { getFlatDocs } from '@/features/docs'

const BASE = MARKETING_URL.replace(/\/$/, '')

const STATIC_ROUTES: Array<{ path: string; priority: number; changeFrequency: MetadataRoute.Sitemap[number]['changeFrequency'] }> = [
  { path: '/',              priority: 1.0, changeFrequency: 'weekly'  },
  { path: '/pricing',       priority: 0.9, changeFrequency: 'monthly' },
  { path: '/integrations',  priority: 0.8, changeFrequency: 'weekly'  },
  { path: '/templates',     priority: 0.7, changeFrequency: 'weekly'  },
  { path: '/blog',          priority: 0.7, changeFrequency: 'weekly'  },
  { path: '/docs',          priority: 0.8, changeFrequency: 'weekly'  },
  { path: '/changelog',     priority: 0.6, changeFrequency: 'weekly'  },
  { path: '/about',         priority: 0.5, changeFrequency: 'monthly' },
  { path: '/contact',       priority: 0.5, changeFrequency: 'monthly' },
  { path: '/security',      priority: 0.6, changeFrequency: 'monthly' },
  { path: '/privacy',       priority: 0.5, changeFrequency: 'monthly' },
  { path: '/terms',         priority: 0.5, changeFrequency: 'monthly' },
  { path: '/cookies',       priority: 0.4, changeFrequency: 'monthly' },
  { path: '/transparency',  priority: 0.5, changeFrequency: 'monthly' },
  { path: '/data-deletion', priority: 0.5, changeFrequency: 'monthly' },
  { path: '/oauth-scopes',  priority: 0.6, changeFrequency: 'monthly' },
]

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date('2026-06-20')

  const staticEntries = STATIC_ROUTES.map((r) => ({
    url: `${BASE}${r.path}`,
    lastModified,
    changeFrequency: r.changeFrequency,
    priority: r.priority,
  }))

  const blogEntries = POSTS.map((p) => ({
    url: `${BASE}/blog/${p.slug}`,
    lastModified,
    changeFrequency: 'monthly' as const,
    priority: 0.5,
  }))

  const docsEntries = getFlatDocs().map((doc) => ({
    url: `${BASE}${doc.href}`,
    lastModified,
    changeFrequency: 'monthly' as const,
    priority: 0.4,
  }))

  return [...staticEntries, ...blogEntries, ...docsEntries]
}

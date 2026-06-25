import { PRODUCT_URL } from '@/shared/constants/routes'
import type { Template, TemplateCategory } from './templates'

/**
 * Shape of one row returned by `GET /api/v1/templates/public` on the
 * API. We project this onto the existing marketing `Template` type so
 * the card component stays unchanged.
 */
type PublicTemplateRow = {
  slug: string
  title: string
  summary: string
  category: string
  steps: number
  tools_required: string[]
  featured: boolean
}

type PublicTemplateResponse = {
  items: PublicTemplateRow[]
  total: number
}

const CATEGORY_LABEL: Record<string, TemplateCategory | string> = {
  sales: 'Sales',
  marketing: 'Marketing',
  engineering: 'Engineering',
  operations: 'Operations',
  support: 'Support',
  internal: 'Internal',
  loops: 'Loops',
  'revenue-ops': 'Revenue ops',
  inbox: 'Inbox',
  reporting: 'Reporting',
}

function prettifyCategory(raw: string): string {
  return CATEGORY_LABEL[raw] ?? raw.charAt(0).toUpperCase() + raw.slice(1)
}

/**
 * Server-side fetch for the marketing templates page. Revalidates every
 * 10 minutes so a freshly seeded template appears without a redeploy,
 * and the previously-rendered HTML stays available if the API is down.
 */
export async function fetchPublicTemplates(): Promise<Template[]> {
  const url = `${PRODUCT_URL}/api/v1/templates/public?limit=60`
  try {
    const res = await fetch(url, { next: { revalidate: 600 } })
    if (!res.ok) return []
    const data = (await res.json()) as PublicTemplateResponse
    return data.items.map((row) => ({
      slug: row.slug,
      title: row.title,
      // The card type expects an opinionated category string; we map the
      // API's lowercase id back to its display label.
      category: prettifyCategory(row.category) as TemplateCategory,
      description: row.summary,
      // The card only reads `.length` for the "N steps" line, so a
      // length-N array of opaque placeholders is enough — saves us from
      // shipping per-node chip metadata in the public payload.
      steps: Array.from({ length: row.steps }, (_, i) => ({
        letter: '',
        color: '',
        label: `step-${i + 1}`,
      })),
    }))
  } catch {
    return []
  }
}

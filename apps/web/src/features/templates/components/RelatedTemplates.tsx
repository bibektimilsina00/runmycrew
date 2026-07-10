import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useTemplates } from '../hooks/useTemplates'
import { TemplateCard } from './TemplateCard'

/**
 * Bottom strip of 3 same-category templates on the detail page.
 * Reuses the existing TemplateCard so the marketing surface here reads
 * identically to the marketplace grid — only the data source changes.
 */

interface RelatedTemplatesProps {
  category: string
  excludeId: string
}

export function RelatedTemplates({ category, excludeId }: RelatedTemplatesProps) {
  const navigate = useNavigate()
  const { data } = useTemplates({ category, limit: 6, sort: 'popular' })

  const items = useMemo(
    () =>
      (data?.items ?? [])
        .filter((t) => t.id !== excludeId)
        .slice(0, 3),
    [data, excludeId],
  )

  if (items.length === 0) return null

  return (
    <section className="flex flex-col gap-4">
      <h2 className="m-0 text-[13.5px] font-semibold text-[var(--text)]">
        Related templates
      </h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <TemplateCard
            key={item.id}
            template={item}
            onClick={() => navigate(APP_ROUTES.TEMPLATE_DETAIL(item.slug))}
          />
        ))}
      </div>
    </section>
  )
}

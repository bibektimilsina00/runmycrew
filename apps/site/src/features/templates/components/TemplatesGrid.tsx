'use client'

import { useMemo, useState } from 'react'
import { type Template } from '../data/templates'
import { TemplateCard } from './TemplateCard'

export function TemplatesGrid({ templates }: { templates: Template[] }) {
  // Derive the filter pill set from whatever the API actually returned
  // so we never advertise a category that has zero templates behind it.
  const categories = useMemo(
    () => Array.from(new Set(templates.map((t) => t.category))).sort(),
    [templates],
  )
  const [cat, setCat] = useState<string>('All')
  const list = cat === 'All' ? templates : templates.filter((t) => t.category === cat)

  if (templates.length === 0) {
    return (
      <div className="rounded-[10px] border border-dashed border-border bg-card/30 px-6 py-12 text-center">
        <p className="m-0 text-[14px] text-muted-foreground">
          No templates published yet — check back soon.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-center gap-1.5">
        <FilterPill label="All" active={cat === 'All'} onClick={() => setCat('All')} />
        {categories.map((c) => (
          <FilterPill key={c} label={c} active={cat === c} onClick={() => setCat(c)} />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {list.map((t, i) => (
          <TemplateCard key={t.slug} t={t} idx={i} />
        ))}
      </div>
    </div>
  )
}

function FilterPill({
  label,
  active,
  onClick,
}: {
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex h-[30px] items-center rounded-[7px] border px-[12px] text-[13px] font-medium transition-colors ${
        active
          ? 'border-primary bg-primary text-primary-foreground'
          : 'border-border bg-card/30 text-muted-foreground hover:border-foreground/30 hover:text-foreground'
      }`}
    >
      {label}
    </button>
  )
}

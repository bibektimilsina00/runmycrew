'use client'

import { useState } from 'react'
import { TEMPLATES, TEMPLATE_CATEGORIES, type TemplateCategory } from '../data/templates'
import { TemplateCard } from './TemplateCard'

export function TemplatesGrid() {
  const [cat, setCat] = useState<TemplateCategory | 'All'>('All')
  const list = cat === 'All' ? TEMPLATES : TEMPLATES.filter((t) => t.category === cat)

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-center gap-1.5">
        <FilterPill label="All" active={cat === 'All'} onClick={() => setCat('All')} />
        {TEMPLATE_CATEGORIES.map((c) => (
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

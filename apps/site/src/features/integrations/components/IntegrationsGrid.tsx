'use client'

import { useState } from 'react'
import { INTEGRATIONS, INTEGRATION_CATEGORIES, type IntegrationCategory } from '../data/integrations'
import { IntegrationCard } from './IntegrationCard'

/**
 * Grid + category pill filter. "All" stays at the front so the page
 * still feels alive when no category is selected.
 */
export function IntegrationsGrid() {
  const [cat, setCat] = useState<IntegrationCategory | 'All'>('All')
  const list = cat === 'All' ? INTEGRATIONS : INTEGRATIONS.filter((i) => i.category === cat)

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-center gap-1.5">
        <FilterPill label="All" active={cat === 'All'} onClick={() => setCat('All')} />
        {INTEGRATION_CATEGORIES.map((c) => (
          <FilterPill key={c} label={c} active={cat === c} onClick={() => setCat(c)} />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {list.map((i) => (
          <IntegrationCard key={i.slug} i={i} />
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
          ? 'border-foreground bg-foreground text-background'
          : 'border-border bg-card/30 text-muted-foreground hover:border-foreground/30 hover:text-foreground'
      }`}
    >
      {label}
    </button>
  )
}

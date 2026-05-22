import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useTemplates } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'

const CATEGORIES = ['All', 'Revenue ops', 'Engineering', 'Inbox', 'Reporting']

export function Templates() {
  const { items } = useTemplates()
  const [cat, setCat] = useState('All')

  const filtered = cat === 'All' ? items : items.filter(t => t.label === cat)

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Curated · by fuse team</span>
          <h1>Templates</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Plus /> Submit template</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {CATEGORIES.map(c => (
            <button key={c} className={`filter-tab${cat === c ? ' active' : ''}`} onClick={() => setCat(c)}>
              {c}
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input placeholder="Search templates" />
          </div>
        </div>
      </div>

      <div className="tpl-grid">
        {filtered.map(t => (
          <TemplateCard key={t.idx} template={t} />
        ))}
      </div>
    </div>
  )
}

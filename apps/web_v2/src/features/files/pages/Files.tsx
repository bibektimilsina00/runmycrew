import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useFiles } from '../hooks/useFiles'
import { FilesList } from '../components/FilesList'

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'generated', label: 'Generated' },
  { id: 'uploaded', label: 'Uploaded' },
  { id: 'attachments', label: 'Attachments' },
]

export function Files() {
  const { items } = useFiles()
  const [filter, setFilter] = useState('all')

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · 124 files · 412 MB used</span>
          <h1>Files</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Folder /> New folder</button>
          <button className="btn btn-primary"><Icons.Plus /> Upload</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {FILTERS.map(f => (
            <button key={f.id} className={`filter-tab${filter === f.id ? ' active' : ''}`} onClick={() => setFilter(f.id)}>
              {f.label}
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input placeholder="Search files" />
          </div>
          <button className="icon-btn" title="Sort"><Icons.Sort /></button>
        </div>
      </div>

      <FilesList items={items} />
    </div>
  )
}

import { Icons } from '@/shared/components/icons'
import type { FileItem } from '../types/filesTypes'

interface Props { items: FileItem[] }

export function FilesList({ items }: Props) {
  return (
    <div className="panel">
      <div className="table table-files">
        <div className="table-head">
          <span></span>
          <span>Name</span>
          <span>Size</span>
          <span>Source</span>
          <span>Uploaded</span>
          <span></span>
        </div>
        {items.map(f => (
          <div key={f.id} className="table-row">
            <span className={`file-icon ${f.ext}`}>{f.ext.toUpperCase()}</span>
            <span className="row-name">{f.name}</span>
            <span className="row-mono">{f.size}</span>
            <span className="row-owner">{f.source}</span>
            <span className="row-mono">{f.uploaded}</span>
            <span className="caret"><Icons.CaretRight /></span>
          </div>
        ))}
      </div>
    </div>
  )
}

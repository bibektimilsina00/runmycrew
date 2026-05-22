import { Icons } from '@/shared/components/icons'
import type { DataTable } from '../types/tablesTypes'

interface Props { items: DataTable[] }

export function TablesTable({ items }: Props) {
  return (
    <div className="panel">
      <div className="table table-tables">
        <div className="table-head">
          <span></span>
          <span>Name</span>
          <span>Rows</span>
          <span>Cols</span>
          <span>Source</span>
          <span>Updated</span>
          <span>Owner</span>
          <span></span>
        </div>
        {items.map(t => (
          <div key={t.id} className="table-row">
            <span className="row-leading"><Icons.Table /></span>
            <span className="row-name mono">{t.name}</span>
            <span className="row-mono">{t.rows}</span>
            <span className="row-mono">{t.cols}</span>
            <span className="row-owner">{t.source}</span>
            <span className="row-mono">{t.updated}</span>
            <span className="row-owner">{t.owner}</span>
            <span className="caret"><Icons.CaretRight /></span>
          </div>
        ))}
      </div>
    </div>
  )
}

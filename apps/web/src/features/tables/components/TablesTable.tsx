import { Empty } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import type { DataTable } from '../types/tablesTypes'
import { formatCount, timeAgo } from '../utils/tableFormat'

interface Props {
  items: DataTable[]
  isLoading?: boolean
  onOpen: (table: DataTable) => void
  onDelete: (table: DataTable) => void
}

export function TablesTable({ items, isLoading, onOpen, onDelete }: Props) {
  return (
    <div className="panel flex-1 min-h-0 flex flex-col">
      <div className="table table-tables flex-1 min-h-0">
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
        {isLoading ? (
          <div className="table-row">
            <span></span>
            <span className="row-owner">Loading tables...</span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>
        ) : items.length === 0 ? (
          <div className="flex-1 min-h-[360px] border-b border-[var(--border-faint)] flex items-center justify-center">
            <Empty
              icon={<Icons.Table />}
              title="No tables found"
              description="Create a table or import a CSV to start working with structured data."
              className="py-10"
            />
          </div>
        ) : (
          items.map(table => (
            <div key={table.id} className="table-row" onClick={() => onOpen(table)}>
              <span className="row-leading"><Icons.Table /></span>
              <span className="row-name mono">{table.name}</span>
              <span className="row-mono">{formatCount(table.row_count)}</span>
              <span className="row-mono">{formatCount(table.column_count)}</span>
              <span className="row-owner">{table.source}</span>
              <span className="row-mono">{timeAgo(table.updated_at)}</span>
              <span className="row-owner">{table.owner}</span>
              <span className="caret">
                <button
                  type="button"
                  title="Delete table"
                  onClick={event => {
                    event.stopPropagation()
                    onDelete(table)
                  }}
                  className="w-[20px] h-[20px] inline-flex items-center justify-center text-[var(--text-faint)] hover:text-[var(--err)]"
                >
                  <Icons.Trash />
                </button>
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

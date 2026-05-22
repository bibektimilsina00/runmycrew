import { useMemo, useRef, useState } from 'react'
import { Button, Input, Modal, useConfirm, useToast } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import { useCreateTable, useDeleteTable, useImportTableCsv, useTables } from '../hooks/useTables'
import { TablesTable } from '../components/TablesTable'
import { TableEditor } from '../components/TableEditor'
import type { DataTable, TableFilter, TableSort } from '../types/tablesTypes'
import { formatCount } from '../utils/tableFormat'

const FILTERS: { id: TableFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'live', label: 'Live' },
  { id: 'static', label: 'Static' },
  { id: 'archived', label: 'Archived' },
]

export function Tables() {
  const { toast } = useToast()
  const confirm = useConfirm()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { data: items = [], isLoading } = useTables()
  const createTable = useCreateTable()
  const importCsv = useImportTableCsv()
  const deleteTable = useDeleteTable()
  const [filter, setFilter] = useState<TableFilter>('all')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<TableSort>('updated_desc')
  const [createOpen, setCreateOpen] = useState(false)
  const [tableName, setTableName] = useState('')
  const [selectedTableId, setSelectedTableId] = useState<string | null>(null)

  const visibleItems = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    const filtered = items.filter(table => {
      const isImported = table.source.toLowerCase().includes('csv')
      const matchesFilter =
        filter === 'all' ||
        (filter === 'static' && !isImported) ||
        (filter === 'live' && isImported)
      const matchesSearch =
        !normalizedSearch ||
        table.name.toLowerCase().includes(normalizedSearch) ||
        table.source.toLowerCase().includes(normalizedSearch) ||
        table.owner.toLowerCase().includes(normalizedSearch)
      return matchesFilter && matchesSearch
    })

    return [...filtered].sort((a, b) => {
      if (sort === 'name_asc') return a.name.localeCompare(b.name)
      if (sort === 'rows_desc') return b.row_count - a.row_count
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
  }, [filter, items, search, sort])

  const selectedTable = items.find(table => table.id === selectedTableId) ?? null

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!tableName.trim()) return
    try {
      const created = await createTable.mutateAsync({ name: tableName.trim(), description: 'Manual table' })
      toast('Table created', { variant: 'ok' })
      setCreateOpen(false)
      setTableName('')
      setSelectedTableId(created.id)
    } catch {
      toast('Failed to create table', { variant: 'err' })
    }
  }

  const handleImport = async (files: FileList | null) => {
    const file = files?.[0]
    if (!file) return
    try {
      const imported = await importCsv.mutateAsync(file)
      toast('CSV imported', { variant: 'ok' })
      setSelectedTableId(imported.id)
    } catch {
      toast('Failed to import CSV', { variant: 'err' })
    }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleOpen = (table: DataTable) => {
    setSelectedTableId(table.id)
  }

  const handleDelete = async (table: DataTable) => {
    const ok = await confirm({
      title: 'Delete table',
      message: `Delete "${table.name}" and all ${table.row_count} rows? This cannot be undone.`,
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (!ok) return
    try {
      await deleteTable.mutateAsync(table.id)
      toast('Table deleted', { variant: 'ok' })
      if (selectedTableId === table.id) setSelectedTableId(null)
    } catch {
      toast('Failed to delete table', { variant: 'err' })
    }
  }

  const cycleSort = () => {
    setSort(current => {
      if (current === 'updated_desc') return 'name_asc'
      if (current === 'name_asc') return 'rows_desc'
      return 'updated_desc'
    })
  }

  const totalRows = items.reduce((sum, table) => sum + table.row_count, 0)

  return (
    <div className="view-body min-h-full">
      <div className="page-head">
        <div>
          <span className="eyebrow">Data · {items.length} tables · {formatCount(totalRows)} rows</span>
          <h1>Tables</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={() => fileInputRef.current?.click()}>
            <Icons.Download /> {importCsv.isPending ? 'Importing...' : 'Import CSV'}
          </button>
          <button className="btn btn-primary" onClick={() => setCreateOpen(true)}>
            <Icons.Plus /> New table
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={event => handleImport(event.target.files)}
          />
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {FILTERS.map(item => (
            <button key={item.id} className={`filter-tab${filter === item.id ? ' active' : ''}`} onClick={() => setFilter(item.id)}>
              {item.label}
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input placeholder="Search tables" value={search} onChange={event => setSearch(event.target.value)} />
          </div>
          <button className="icon-btn" title={`Sort: ${sortLabel(sort)}`} onClick={cycleSort}><Icons.Sort /></button>
        </div>
      </div>

      {selectedTable ? (
        <TableEditor table={selectedTable} onClose={() => setSelectedTableId(null)} />
      ) : (
        <TablesTable items={visibleItems} isLoading={isLoading} onOpen={handleOpen} onDelete={handleDelete} />
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="New table">
        <form onSubmit={handleCreate} className="flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Table name</label>
            <Input
              value={tableName}
              onChange={event => setTableName(event.target.value)}
              placeholder="e.g. leads, invoices, customers"
              autoFocus
            />
          </div>
          <div className="flex justify-end gap-2 border-t border-[var(--border-faint)] pt-4">
            <Button variant="secondary" type="button" size="sm" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit" size="sm" disabled={createTable.isPending || !tableName.trim()}>
              {createTable.isPending ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

function sortLabel(sort: TableSort): string {
  if (sort === 'name_asc') return 'Name'
  if (sort === 'rows_desc') return 'Rows'
  return 'Updated'
}

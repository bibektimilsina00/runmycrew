import { useMemo, useRef, useState, type FormEvent } from 'react'
import { Button, Input, Modal, useConfirm, useToast } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import { useCreateTable, useDeleteTable, useImportTableCsv, useTables } from '../hooks/useTables'
import { TableEditor } from '../components/TableEditor'
import type { DataTable } from '../types/tablesTypes'
import { formatCount } from '../utils/tableFormat'
import { cn } from '@/lib/cn'

export function Tables() {
  const { toast } = useToast()
  const confirm = useConfirm()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { data: items = [], isLoading } = useTables()
  const createTable = useCreateTable()
  const importCsv = useImportTableCsv()
  const deleteTable = useDeleteTable()
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [tableName, setTableName] = useState('')
  const [selectedTableId, setSelectedTableId] = useState<string | null>(null)

  const visibleItems = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    return items
      .filter(table =>
        !normalizedSearch ||
        table.name.toLowerCase().includes(normalizedSearch) ||
        table.source.toLowerCase().includes(normalizedSearch) ||
        table.owner.toLowerCase().includes(normalizedSearch),
      )
      .sort((a, b) => a.name.localeCompare(b.name))
  }, [items, search])

  const selectedTable = items.find(table => table.id === selectedTableId) ?? null

  const handleCreate = async (event: FormEvent) => {
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

  const totalRows = items.reduce((sum, table) => sum + table.row_count, 0)

  return (
    <div className="h-full min-h-0 flex overflow-hidden bg-[var(--bg)]">
      <aside className="w-48 shrink-0 border-r border-[var(--border-faint)] flex flex-col overflow-hidden bg-[var(--bg)]">
        <div className="flex items-center justify-between border-b border-[var(--border-faint)] px-3 py-3">
          <div className="min-w-0">
            <span className="block text-[12px] font-semibold text-[var(--text)]">Tables</span>
            <span className="block truncate text-[10px] text-[var(--text-faint)]">
              {items.length} tables · {formatCount(totalRows)} rows
            </span>
          </div>
          <button
            onClick={() => setCreateOpen(true)}
            className="flex h-7 w-7 items-center justify-center rounded-[7px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
            title="New table"
          >
            <Icons.Plus className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="border-b border-[var(--border-faint)] p-2">
          <div className="cmd-search inline-search h-8">
            <Icons.Search />
            <input placeholder="Search" value={search} onChange={event => setSearch(event.target.value)} />
          </div>
          <button
            className="mt-2 flex w-full items-center gap-1.5 rounded-[7px] px-2.5 py-1.5 text-left text-[12px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
            onClick={() => fileInputRef.current?.click()}
          >
            <Icons.Download className="h-3.5 w-3.5" /> {importCsv.isPending ? 'Importing...' : 'Import CSV'}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={event => handleImport(event.target.files)}
          />
        </div>

        <div className="flex-1 overflow-y-auto py-1">
          {isLoading ? (
            <div className="px-3 py-2 text-[12px] text-[var(--text-faint)]">Loading...</div>
          ) : visibleItems.length === 0 ? (
            <button
              onClick={() => setCreateOpen(true)}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-[12px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
            >
              <Icons.Plus className="h-3.5 w-3.5" /> New table
            </button>
          ) : (
            visibleItems.map(table => (
              <div key={table.id} className="group relative">
                <button
                  onClick={() => handleOpen(table)}
                  className={cn(
                    'flex w-full items-center gap-2 px-3 py-2 pr-8 text-left text-[12px] transition-colors',
                    table.id === selectedTable?.id
                      ? 'bg-[var(--surface)] text-[var(--text)]'
                      : 'text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
                  )}
                >
                  <Icons.Table className="h-3.5 w-3.5 shrink-0" />
                  <span className="min-w-0 flex-1 truncate">{table.name}</span>
                </button>
                <button
                  type="button"
                  title="Delete table"
                  onClick={() => handleDelete(table)}
                  className="absolute right-2 top-1/2 hidden h-5 w-5 -translate-y-1/2 items-center justify-center rounded text-[var(--text-faint)] transition-colors hover:text-[var(--err)] group-hover:flex"
                >
                  <Icons.Trash className="h-3 w-3" />
                </button>
              </div>
            ))
          )}
        </div>
      </aside>

      <main className="min-w-0 flex-1 overflow-hidden">
        {selectedTable ? (
          <TableEditor table={selectedTable} onClose={() => setSelectedTableId(null)} />
        ) : (
          <div className="flex h-full flex-col items-center justify-center p-8 text-center">
            <Icons.Table className="mx-auto mb-3 h-10 w-10 text-[var(--text-faint)] opacity-40" />
            <p className="mb-1 text-[14px] font-medium text-[var(--text)]">No table selected</p>
            <p className="mb-4 text-[13px] text-[var(--text-faint)]">
              {items.length === 0 ? 'Create your first table to get started' : 'Select a table from the sidebar'}
            </p>
            {items.length === 0 && (
              <button
                onClick={() => setCreateOpen(true)}
                className="flex items-center gap-1.5 rounded-[8px] border border-[var(--border-faint)] px-4 py-2 text-[13px] text-[var(--text-faint)] transition-colors hover:border-[var(--border-soft)] hover:text-[var(--text)]"
              >
                <Icons.Plus className="h-3.5 w-3.5" /> New table
              </button>
            )}
          </div>
        )}
      </main>

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

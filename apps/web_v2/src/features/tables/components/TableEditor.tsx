import { useMemo, useRef, useState, type FormEvent } from 'react'
import { Button, Empty, Input, Modal, useConfirm, useToast } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import { cn } from '@/lib/cn'
import {
  useAddTableColumn,
  useAddTableRow,
  useDeleteTableColumn,
  useDeleteTableRow,
  useImportTableRowsCsv,
  useTableRows,
  useUpdateTableColumn,
  useUpdateTableRow,
} from '../hooks/useTables'
import { tablesAPI } from '../services/tablesAPI'
import {
  TABLE_COLUMN_TYPES,
  type DataTable,
  type TableColumn,
  type TableColumnType,
  type TableRow,
} from '../types/tablesTypes'

interface TableEditorProps {
  table: DataTable
  onClose: () => void
}

interface ColumnFormState {
  name: string
  colType: TableColumnType
  choices: string
}

const emptyColumnForm: ColumnFormState = {
  name: '',
  colType: 'text',
  choices: '',
}

export function TableEditor({ table, onClose }: TableEditorProps) {
  const { toast } = useToast()
  const confirm = useConfirm()
  const importInputRef = useRef<HTMLInputElement>(null)
  const { data, isLoading } = useTableRows(table.id)
  const addColumn = useAddTableColumn(table.id)
  const updateColumn = useUpdateTableColumn(table.id)
  const deleteColumn = useDeleteTableColumn(table.id)
  const addRow = useAddTableRow(table.id)
  const deleteRow = useDeleteTableRow(table.id)
  const importRowsCsv = useImportTableRowsCsv(table.id)
  const [columnModalOpen, setColumnModalOpen] = useState(false)
  const [editingColumn, setEditingColumn] = useState<TableColumn | null>(null)
  const [columnForm, setColumnForm] = useState<ColumnFormState>(emptyColumnForm)

  const columns = useMemo(
    () => [...(data?.columns ?? [])].sort((a, b) => a.position - b.position),
    [data?.columns],
  )
  const rows = useMemo(
    () => [...(data?.rows ?? [])].sort((a, b) => (a.position ?? 0) - (b.position ?? 0)),
    [data?.rows],
  )

  const openNewColumn = () => {
    setEditingColumn(null)
    setColumnForm(emptyColumnForm)
    setColumnModalOpen(true)
  }

  const openEditColumn = (column: TableColumn) => {
    setEditingColumn(column)
    setColumnForm({
      name: column.name,
      colType: column.col_type,
      choices: readChoices(column).join(', '),
    })
    setColumnModalOpen(true)
  }

  const handleColumnSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const name = columnForm.name.trim()
    if (!name) return
    const payload = {
      name,
      col_type: columnForm.colType,
      options: columnForm.colType === 'select' ? { choices: parseChoices(columnForm.choices) } : null,
    }

    try {
      if (editingColumn) {
        await updateColumn.mutateAsync({ columnId: editingColumn.id, data: payload })
        toast('Column updated', { variant: 'ok' })
      } else {
        await addColumn.mutateAsync(payload)
        toast('Column added', { variant: 'ok' })
      }
      setColumnModalOpen(false)
    } catch {
      toast('Failed to save column', { variant: 'err' })
    }
  }

  const handleDeleteColumn = async () => {
    if (!editingColumn) return
    const ok = await confirm({
      title: 'Delete column',
      message: `Delete "${editingColumn.name}" from this table? Existing values in this column will be removed from view.`,
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (!ok) return
    try {
      await deleteColumn.mutateAsync(editingColumn.id)
      toast('Column deleted', { variant: 'ok' })
      setColumnModalOpen(false)
    } catch {
      toast('Failed to delete column', { variant: 'err' })
    }
  }

  const handleAddRow = async () => {
    try {
      await addRow.mutateAsync({ data: {} })
      toast('Row added', { variant: 'ok' })
    } catch {
      toast('Failed to add row', { variant: 'err' })
    }
  }

  const handleDeleteRow = async (row: TableRow) => {
    const ok = await confirm({
      title: 'Delete row',
      message: 'Delete this row? This cannot be undone.',
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (!ok) return
    try {
      await deleteRow.mutateAsync(row.id)
      toast('Row deleted', { variant: 'ok' })
    } catch {
      toast('Failed to delete row', { variant: 'err' })
    }
  }

  const handleImportRows = async (files: FileList | null) => {
    const file = files?.[0]
    if (!file) return
    try {
      const result = await importRowsCsv.mutateAsync(file)
      toast(`Imported ${result.imported} rows`, { variant: 'ok' })
    } catch {
      toast('Failed to import rows', { variant: 'err' })
    }
    if (importInputRef.current) importInputRef.current.value = ''
  }

  const handleExport = async () => {
    try {
      const blob = await tablesAPI.exportCsvBlob(table.id)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${table.name}.csv`
      link.click()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch {
      toast('Failed to export table', { variant: 'err' })
    }
  }

  return (
    <section className="panel min-h-[520px] flex flex-col overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-[var(--border-faint)] px-4 py-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <button className="icon-btn" title="Back to tables" onClick={onClose}>
              <Icons.CaretLeft />
            </button>
            <div className="min-w-0">
              <h2 className="truncate text-[15px] font-semibold text-[var(--text)]">{table.name}</h2>
              <p className="text-[12px] text-[var(--text-mute)]">
                {rows.length} rows · {columns.length} columns
              </p>
            </div>
          </div>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={() => importInputRef.current?.click()}>
            <Icons.Download /> {importRowsCsv.isPending ? 'Importing...' : 'Import CSV'}
          </button>
          <button className="btn btn-secondary" onClick={handleExport}>
            <Icons.Download /> Export CSV
          </button>
          <button className="btn btn-secondary" onClick={openNewColumn}>
            <Icons.Plus /> New column
          </button>
          <button className="btn btn-primary" onClick={handleAddRow} disabled={addRow.isPending}>
            <Icons.Plus /> Add row
          </button>
          <input
            ref={importInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={event => handleImportRows(event.target.files)}
          />
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-auto">
        {isLoading ? (
          <div className="flex h-full min-h-[360px] items-center justify-center text-sm text-[var(--text-mute)]">
            Loading table...
          </div>
        ) : columns.length === 0 ? (
          <Empty
            icon={<Icons.Table />}
            title="No columns"
            description="Add a column before entering row data."
            className="min-h-[420px]"
          />
        ) : (
          <TableGrid
            columns={columns}
            rows={rows}
            onEditColumn={openEditColumn}
            onDeleteRow={handleDeleteRow}
            tableId={table.id}
          />
        )}
      </div>

      <Modal
        open={columnModalOpen}
        onClose={() => setColumnModalOpen(false)}
        title={editingColumn ? 'Edit column' : 'New column'}
      >
        <form onSubmit={handleColumnSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Column name</label>
            <Input
              value={columnForm.name}
              onChange={event => setColumnForm(current => ({ ...current, name: event.target.value }))}
              placeholder="e.g. Email, Amount, Status"
              autoFocus
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-[12px] font-medium text-[var(--text-mute)]">Column type</label>
            <select
              className="h-9 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none focus:border-[var(--border-soft)]"
              value={columnForm.colType}
              onChange={event => setColumnForm(current => ({ ...current, colType: event.target.value as TableColumnType }))}
            >
              {TABLE_COLUMN_TYPES.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          {columnForm.colType === 'select' && (
            <div className="flex flex-col gap-1.5">
              <label className="text-[12px] font-medium text-[var(--text-mute)]">Choices</label>
              <Input
                value={columnForm.choices}
                onChange={event => setColumnForm(current => ({ ...current, choices: event.target.value }))}
                placeholder="New, Qualified, Closed"
              />
            </div>
          )}
          <div className="flex items-center justify-between border-t border-[var(--border-faint)] pt-4">
            {editingColumn ? (
              <Button variant="danger" type="button" size="sm" onClick={handleDeleteColumn} loading={deleteColumn.isPending}>
                Delete
              </Button>
            ) : <span />}
            <div className="flex gap-2">
              <Button variant="secondary" type="button" size="sm" onClick={() => setColumnModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                type="submit"
                size="sm"
                disabled={!columnForm.name.trim()}
                loading={addColumn.isPending || updateColumn.isPending}
              >
                Save
              </Button>
            </div>
          </div>
        </form>
      </Modal>
    </section>
  )
}

interface TableGridProps {
  columns: TableColumn[]
  rows: TableRow[]
  onEditColumn: (column: TableColumn) => void
  onDeleteRow: (row: TableRow) => void
  tableId: string
}

function TableGrid({ columns, rows, onEditColumn, onDeleteRow, tableId }: TableGridProps) {
  return (
    <table className="min-w-full border-collapse text-left text-sm">
      <thead className="sticky top-0 z-10 bg-[var(--surface)]">
        <tr>
          <th className="w-12 border-b border-r border-[var(--border-faint)] px-3 py-2 text-[11px] font-semibold uppercase text-[var(--text-faint)]">
            #
          </th>
          {columns.map(column => (
            <th
              key={column.id}
              className="min-w-[180px] border-b border-r border-[var(--border-faint)] px-0 py-0"
            >
              <button
                type="button"
                className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-[12px] font-semibold text-[var(--text)] hover:bg-[var(--surface-2)]"
                onClick={() => onEditColumn(column)}
                title="Edit column"
              >
                <span className="truncate">{column.name}</span>
                <span className="text-[10px] font-medium uppercase text-[var(--text-faint)]">{column.col_type}</span>
              </button>
            </th>
          ))}
          <th className="w-12 border-b border-[var(--border-faint)] px-2 py-2" />
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 ? (
          <tr>
            <td colSpan={columns.length + 2} className="h-[320px]">
              <Empty
                icon={<Icons.Table />}
                title="No rows"
                description="Add a row or import a CSV to start editing cells."
              />
            </td>
          </tr>
        ) : (
          rows.map((row, index) => (
            <tr key={row.id} className="group hover:bg-[var(--surface)]">
              <td className="border-b border-r border-[var(--border-faint)] px-3 py-2 text-[12px] text-[var(--text-faint)]">
                {index + 1}
              </td>
              {columns.map(column => (
                <td key={column.id} className="border-b border-r border-[var(--border-faint)] p-0">
                  <EditableCell
                    key={`${row.id}:${column.id}:${formatCellValue(row.data[column.id])}`}
                    tableId={tableId}
                    row={row}
                    column={column}
                  />
                </td>
              ))}
              <td className="border-b border-[var(--border-faint)] px-2 py-2">
                <button
                  type="button"
                  title="Delete row"
                  className="flex h-7 w-7 items-center justify-center rounded-[6px] text-[var(--text-faint)] opacity-0 hover:bg-[var(--surface-2)] hover:text-[var(--err)] group-hover:opacity-100"
                  onClick={() => onDeleteRow(row)}
                >
                  <Icons.Trash />
                </button>
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  )
}

interface EditableCellProps {
  tableId: string
  row: TableRow
  column: TableColumn
}

function EditableCell({ tableId, row, column }: EditableCellProps) {
  const { toast } = useToast()
  const updateRow = useUpdateTableRow(tableId)
  const value = row.data[column.id]
  const [draft, setDraft] = useState(formatCellValue(value))

  const commit = async (nextValue: unknown) => {
    if (Object.is(nextValue, value)) return
    try {
      await updateRow.mutateAsync({ rowId: row.id, data: { data: { [column.id]: nextValue } } })
    } catch {
      toast('Failed to update cell', { variant: 'err' })
      setDraft(formatCellValue(value))
    }
  }

  if (column.col_type === 'boolean') {
    return (
      <label className="flex min-h-[38px] items-center px-3">
        <input
          type="checkbox"
          checked={value === true}
          onChange={event => commit(event.target.checked)}
          className="h-4 w-4 rounded border-[var(--border-faint)]"
        />
      </label>
    )
  }

  if (column.col_type === 'select') {
    return (
      <select
        value={draft}
        onChange={event => {
          setDraft(event.target.value)
          commit(event.target.value)
        }}
        className="min-h-[38px] w-full bg-transparent px-3 text-sm text-[var(--text)] outline-none focus:bg-[var(--surface)]"
      >
        <option value=""></option>
        {readChoices(column).map(choice => (
          <option key={choice} value={choice}>{choice}</option>
        ))}
      </select>
    )
  }

  return (
    <input
      value={draft}
      type={inputType(column.col_type)}
      onChange={event => setDraft(event.target.value)}
      onBlur={() => commit(coerceCellValue(draft, column.col_type))}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.currentTarget.blur()
        }
        if (event.key === 'Escape') {
          setDraft(formatCellValue(value))
          event.currentTarget.blur()
        }
      }}
      className={cn(
        'min-h-[38px] w-full bg-transparent px-3 text-sm text-[var(--text)] outline-none',
        'focus:bg-[var(--surface)] focus:shadow-[inset_0_0_0_1px_var(--border-soft)]',
      )}
    />
  )
}

function inputType(type: TableColumnType): string {
  if (type === 'number') return 'number'
  if (type === 'date') return 'date'
  if (type === 'email') return 'email'
  if (type === 'url') return 'url'
  if (type === 'phone') return 'tel'
  return 'text'
}

function coerceCellValue(value: string, type: TableColumnType): unknown {
  if (type === 'number') {
    if (value.trim() === '') return ''
    const numeric = Number(value)
    return Number.isFinite(numeric) ? numeric : value
  }
  return value
}

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return JSON.stringify(value)
}

function parseChoices(value: string): string[] {
  return value
    .split(',')
    .map(choice => choice.trim())
    .filter(Boolean)
}

function readChoices(column: TableColumn): string[] {
  const choices = column.options?.choices
  return Array.isArray(choices) ? choices.filter((choice): choice is string => typeof choice === 'string') : []
}

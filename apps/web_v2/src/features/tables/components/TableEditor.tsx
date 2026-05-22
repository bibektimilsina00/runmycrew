import { useMemo, useRef, useState, type Dispatch, type FormEvent, type SetStateAction } from 'react'
import {
  AlignLeft,
  Calendar,
  Check,
  Hash,
  Link,
  List,
  Mail,
  Phone,
  Type,
  X,
} from 'lucide-react'
import { Empty, useConfirm, useToast } from '@/shared/components'
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
  required: boolean
  defaultValue: string
  choices: string[]
  newChoice: string
}

const emptyColumnForm: ColumnFormState = {
  name: '',
  colType: 'text',
  required: false,
  defaultValue: '',
  choices: [],
  newChoice: '',
}

const COLUMN_TYPE_DEFS = [
  { type: 'text', label: 'Text', icon: Type, description: 'Single or multi-line text' },
  { type: 'number', label: 'Number', icon: Hash, description: 'Integer or decimal values' },
  { type: 'boolean', label: 'Checkbox', icon: Check, description: 'True / false toggle' },
  { type: 'date', label: 'Date', icon: Calendar, description: 'Date and optional time' },
  { type: 'select', label: 'Select', icon: List, description: 'Single choice from options' },
  { type: 'url', label: 'URL', icon: Link, description: 'Web link' },
  { type: 'email', label: 'Email', icon: Mail, description: 'Email address' },
  { type: 'phone', label: 'Phone', icon: Phone, description: 'Phone number' },
  { type: 'textarea', label: 'Long text', icon: AlignLeft, description: 'Multi-line text area' },
] satisfies {
  type: TableColumnType
  label: string
  icon: typeof Type
  description: string
}[]

const COLUMN_ICON_BY_TYPE = Object.fromEntries(
  COLUMN_TYPE_DEFS.map(typeDef => [typeDef.type, typeDef.icon]),
) as Record<TableColumnType, typeof Type>

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
  const [columnPanelOpen, setColumnPanelOpen] = useState(false)
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
    setColumnPanelOpen(true)
  }

  const openEditColumn = (column: TableColumn) => {
    setEditingColumn(column)
    const options = column.options ?? {}
    setColumnForm({
      name: column.name,
      colType: column.col_type,
      required: options.required === true,
      defaultValue: typeof options.default === 'string' ? options.default : '',
      choices: readChoices(column),
      newChoice: '',
    })
    setColumnPanelOpen(true)
  }

  const handleColumnSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const name = columnForm.name.trim()
    if (!name) return
    const payload = {
      name,
      col_type: columnForm.colType,
      options: buildColumnOptions(columnForm),
    }

    try {
      if (editingColumn) {
        await updateColumn.mutateAsync({ columnId: editingColumn.id, data: payload })
        toast('Column updated', { variant: 'ok' })
      } else {
        await addColumn.mutateAsync(payload)
        toast('Column added', { variant: 'ok' })
      }
      setColumnPanelOpen(false)
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
      setColumnPanelOpen(false)
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
    <section className="h-full min-h-0 flex overflow-hidden bg-[var(--bg)]">
      <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between gap-3 border-b border-[var(--border-faint)] px-4 py-2 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <button className="icon-btn" title="Back to tables" onClick={onClose}>
              <Icons.CaretLeft />
            </button>
            <span className="text-[13px] text-[var(--text-faint)]">Tables</span>
            <span className="text-[var(--text-faint)]">/</span>
            <span className="truncate text-[13px] font-medium text-[var(--text)]">{table.name}</span>
            <Icons.Caret className="h-3.5 w-3.5 text-[var(--text-faint)]" />
          </div>
          <div className="flex items-center gap-1 text-[11px] text-[var(--text-faint)]">
            {rows.length} rows · {columns.length} columns
          </div>
        </div>

        <div className="flex items-center justify-between border-b border-[var(--border-faint)] px-4 py-2 shrink-0">
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[12px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]">
              <Icons.Sort className="h-3.5 w-3.5" /> Filter
            </button>
            <button className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[12px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]">
              <Icons.Sort className="h-3.5 w-3.5" /> Sort
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[12px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
              onClick={() => importInputRef.current?.click()}
            >
              <Icons.Download className="h-3.5 w-3.5" /> {importRowsCsv.isPending ? 'Importing...' : 'Import CSV'}
            </button>
            <button
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[12px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
              onClick={handleExport}
            >
              <Icons.Download className="h-3.5 w-3.5" /> Export CSV
            </button>
            <button
              className={cn(
                'flex items-center gap-1.5 rounded-[8px] border px-2.5 py-1.5 text-[12px] transition-colors',
                columnPanelOpen && !editingColumn
                  ? 'border-[var(--border-soft)] bg-[var(--surface)] text-[var(--text)]'
                  : 'border-[var(--border-faint)] text-[var(--text-faint)] hover:border-[var(--border-soft)] hover:text-[var(--text)]',
              )}
              onClick={openNewColumn}
            >
              <Icons.Plus className="h-3.5 w-3.5" /> New column
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
            <div className="flex h-full min-h-[360px] items-center justify-center text-sm text-[var(--text-faint)]">
              Loading...
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
              onAddColumn={openNewColumn}
              onAddRow={handleAddRow}
              tableId={table.id}
              addingRow={addRow.isPending}
            />
          )}
        </div>
      </div>

      {columnPanelOpen && (
        <ColumnPanel
          key={editingColumn?.id ?? 'new-column'}
          editingColumn={editingColumn}
          form={columnForm}
          setForm={setColumnForm}
          onClose={() => setColumnPanelOpen(false)}
          onSubmit={handleColumnSubmit}
          onDelete={handleDeleteColumn}
          saving={addColumn.isPending || updateColumn.isPending}
          deleting={deleteColumn.isPending}
        />
      )}
    </section>
  )
}

interface ColumnPanelProps {
  editingColumn: TableColumn | null
  form: ColumnFormState
  setForm: Dispatch<SetStateAction<ColumnFormState>>
  onClose: () => void
  onSubmit: (event: FormEvent) => void
  onDelete: () => void
  saving: boolean
  deleting: boolean
}

function ColumnPanel({
  editingColumn,
  form,
  setForm,
  onClose,
  onSubmit,
  onDelete,
  saving,
  deleting,
}: ColumnPanelProps) {
  return (
    <form
      onSubmit={onSubmit}
      className="w-72 shrink-0 border-l border-[var(--border-faint)] bg-[var(--bg-2)] flex flex-col overflow-hidden shadow-[-16px_0_40px_-28px_oklch(0_0_0/0.55)]"
    >
      <div className="flex items-center justify-between border-b border-[var(--border-faint)] px-4 py-3.5">
        <h3 className="text-[13px] font-semibold text-[var(--text)]">
          {editingColumn ? 'Edit column' : 'New column'}
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="text-[var(--text-faint)] transition-colors hover:text-[var(--text)]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-5">
        <div>
          <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-[var(--text-faint)]">
            Column Name
          </label>
          <input
            autoFocus
            value={form.name}
            onChange={event => setForm(current => ({ ...current, name: event.target.value }))}
            placeholder="Column name"
            className="w-full rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2 text-[13px] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)] focus:border-[var(--border-soft)]"
          />
        </div>

        <div>
          <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-[var(--text-faint)]">
            Data Type
          </label>
          <div className="flex flex-col gap-1">
            {COLUMN_TYPE_DEFS.map(typeDef => {
              const Icon = typeDef.icon
              const active = form.colType === typeDef.type
              return (
                <button
                  key={typeDef.type}
                  type="button"
                  onClick={() => setForm(current => ({ ...current, colType: typeDef.type }))}
                  className={cn(
                    'flex w-full items-center gap-2.5 rounded-[8px] border px-3 py-2 text-left transition-colors',
                    active
                      ? 'border-[var(--border-soft)] bg-[var(--surface)] text-[var(--text)]'
                      : 'border-transparent text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)]',
                  )}
                >
                  <Icon className="h-3.5 w-3.5 shrink-0" />
                  <span className="min-w-0 flex-1">
                    <span className="block text-[12px] font-medium leading-none">{typeDef.label}</span>
                    <span className="mt-0.5 block text-[10px] text-[var(--text-faint)]">{typeDef.description}</span>
                  </span>
                  {active && <Check className="h-3.5 w-3.5 shrink-0" />}
                </button>
              )
            })}
          </div>
        </div>

        {form.colType === 'select' && (
          <div>
            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-[var(--text-faint)]">
              Options
            </label>
            <div className="mb-2 flex flex-col gap-1">
              {form.choices.map((choice, index) => (
                <div
                  key={`${choice}:${index}`}
                  className="group flex items-center gap-2 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-2.5 py-1.5"
                >
                  <div className="h-2 w-2 shrink-0 rounded-full bg-[var(--ok)]" />
                  <span className="flex-1 truncate text-[12px] text-[var(--text)]">{choice}</span>
                  <button
                    type="button"
                    onClick={() => setForm(current => ({
                      ...current,
                      choices: current.choices.filter((_, choiceIndex) => choiceIndex !== index),
                    }))}
                    className="text-[var(--text-faint)] opacity-0 transition-all hover:text-[var(--err)] group-hover:opacity-100"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                value={form.newChoice}
                onChange={event => setForm(current => ({ ...current, newChoice: event.target.value }))}
                onKeyDown={event => {
                  if (event.key !== 'Enter') return
                  event.preventDefault()
                  addChoice(setForm)
                }}
                placeholder="Add option..."
                className="min-w-0 flex-1 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-2.5 py-1.5 text-[12px] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)] focus:border-[var(--border-soft)]"
              />
              <button
                type="button"
                onClick={() => addChoice(setForm)}
                className="rounded-[8px] border border-[var(--border-faint)] px-2.5 py-1.5 text-[var(--text-faint)] transition-colors hover:text-[var(--text)]"
              >
                <Icons.Plus className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}

        <div>
          <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-[var(--text-faint)]">
            Constraints
          </label>
          <button
            type="button"
            onClick={() => setForm(current => ({ ...current, required: !current.required }))}
            className="flex items-center gap-2.5"
          >
            <span
              className={cn(
                'relative h-4 w-8 rounded-full transition-colors',
                form.required ? 'bg-[var(--text)]' : 'border border-[var(--border-faint)] bg-[var(--surface)]',
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 h-3 w-3 rounded-full bg-[var(--bg)] transition-transform',
                  form.required ? 'translate-x-4' : 'translate-x-0.5',
                )}
              />
            </span>
            <span className="text-[12px] text-[var(--text-faint)]">Required</span>
          </button>
        </div>

        {form.colType !== 'boolean' && form.colType !== 'select' && (
          <div>
            <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wide text-[var(--text-faint)]">
              Default Value
            </label>
            <input
              value={form.defaultValue}
              onChange={event => setForm(current => ({ ...current, defaultValue: event.target.value }))}
              placeholder="Leave empty for none"
              className="w-full rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2 text-[13px] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)] focus:border-[var(--border-soft)]"
            />
          </div>
        )}
      </div>

      <div className="flex gap-2 border-t border-[var(--border-faint)] p-4">
        {editingColumn ? (
          <button
            type="button"
            onClick={onDelete}
            disabled={deleting}
            className="rounded-[8px] border border-[var(--border-faint)] px-3 py-2 text-[12px] text-[var(--err)] transition-colors hover:bg-[var(--surface)] disabled:opacity-40"
          >
            Delete
          </button>
        ) : null}
        <button
          type="button"
          onClick={onClose}
          className="flex-1 rounded-[8px] border border-[var(--border-faint)] py-2 text-[12px] text-[var(--text-faint)] transition-colors hover:text-[var(--text)]"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving || !form.name.trim()}
          className="flex-1 rounded-[8px] bg-[var(--text)] py-2 text-[12px] font-semibold text-[var(--bg)] transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {saving ? 'Saving...' : editingColumn ? 'Save changes' : 'Add column'}
        </button>
      </div>
    </form>
  )
}

interface TableGridProps {
  columns: TableColumn[]
  rows: TableRow[]
  onEditColumn: (column: TableColumn) => void
  onDeleteRow: (row: TableRow) => void
  onAddColumn: () => void
  onAddRow: () => void
  tableId: string
  addingRow: boolean
}

function TableGrid({
  columns,
  rows,
  onEditColumn,
  onDeleteRow,
  onAddColumn,
  onAddRow,
  tableId,
  addingRow,
}: TableGridProps) {
  const columnWidth = 180

  return (
    <table className="border-collapse text-left" style={{ minWidth: (columns.length + 1) * columnWidth + 48 }}>
      <thead className="sticky top-0 z-10">
        <tr>
          <th className="w-12 border-b border-r border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2.5">
            <input type="checkbox" className="opacity-0" />
          </th>
          {columns.map(column => (
            <th
              key={column.id}
              className="border-b border-r border-[var(--border-faint)] bg-[var(--surface)] text-left transition-colors hover:bg-[var(--surface-2)]"
              style={{ width: columnWidth, minWidth: columnWidth }}
            >
              <button
                type="button"
                className="flex w-full items-center gap-1.5 px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--text-faint)]"
                onClick={() => onEditColumn(column)}
                title="Edit column"
              >
                <ColumnTypeIcon type={column.col_type} />
                <span className="truncate">{column.name}</span>
              </button>
            </th>
          ))}
          <th className="border-b border-[var(--border-faint)] bg-[var(--surface)] px-3 py-2.5" style={{ width: columnWidth }}>
            <button
              type="button"
              onClick={onAddColumn}
              className="flex items-center gap-1 text-[11px] text-[var(--text-faint)] transition-colors hover:text-[var(--text)]"
            >
              <Icons.Plus className="h-3.5 w-3.5" /> New column
            </button>
          </th>
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
            <tr key={row.id} className="group border-b border-[var(--border-faint)] transition-colors hover:bg-[var(--surface)]" style={{ height: 36 }}>
              <td className="w-12 border-r border-[var(--border-faint)] px-3 text-center text-[11px] text-[var(--text-faint)]">
                <span className="group-hover:hidden">{index + 1}</span>
                <button
                  type="button"
                  onClick={() => onDeleteRow(row)}
                  className="mx-auto hidden text-[var(--text-faint)] transition-colors hover:text-[var(--err)] group-hover:block"
                >
                  <Icons.Trash className="h-3 w-3" />
                </button>
              </td>
              {columns.map(column => (
                <td key={column.id} className="border-r border-[var(--border-faint)] p-0" style={{ width: columnWidth, height: 36 }}>
                  <EditableCell
                    key={`${row.id}:${column.id}:${formatCellValue(row.data[column.id])}`}
                    tableId={tableId}
                    row={row}
                    column={column}
                  />
                </td>
              ))}
              <td />
            </tr>
          ))
        )}
        <tr>
          <td colSpan={columns.length + 2} className="px-3 py-2">
            <button
              type="button"
              onClick={onAddRow}
              disabled={addingRow}
              className="flex items-center gap-1.5 text-[12px] text-[var(--text-faint)] transition-colors hover:text-[var(--text)] disabled:opacity-40"
            >
              <Icons.Plus className="h-3.5 w-3.5" /> New row
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  )
}

function ColumnTypeIcon({ type }: { type: TableColumnType }) {
  const Icon = COLUMN_ICON_BY_TYPE[type] ?? Type
  return <Icon className="h-3 w-3 shrink-0" />
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
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(formatCellValue(value))

  const commit = async (nextValue: unknown) => {
    setEditing(false)
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
      <label className="flex h-full min-h-9 items-center px-3">
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
        className="h-full min-h-9 w-full bg-transparent px-3 text-[13px] text-[var(--text)] outline-none focus:bg-[var(--surface)]"
      >
        <option value=""></option>
        {readChoices(column).map(choice => (
          <option key={choice} value={choice}>{choice}</option>
        ))}
      </select>
    )
  }

  if (!editing) {
    return (
      <div
        className="h-full min-h-9 w-full cursor-text truncate px-3 py-2 text-[13px] text-[var(--text)]"
        onDoubleClick={() => setEditing(true)}
      >
        {formatCellValue(value)}
      </div>
    )
  }

  return (
    <input
      autoFocus
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
          setEditing(false)
        }
      }}
      className={cn(
        'h-full min-h-9 w-full bg-[var(--surface-2)] px-3 py-2 text-[13px] text-[var(--text)] outline-none',
        'shadow-[inset_0_0_0_1px_var(--border-soft)]',
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

function readChoices(column: TableColumn): string[] {
  const choices = column.options?.choices
  return Array.isArray(choices) ? choices.filter((choice): choice is string => typeof choice === 'string') : []
}

function addChoice(setForm: Dispatch<SetStateAction<ColumnFormState>>) {
  setForm(current => {
    const choice = current.newChoice.trim()
    if (!choice) return current
    return {
      ...current,
      choices: [...current.choices, choice],
      newChoice: '',
    }
  })
}

function buildColumnOptions(form: ColumnFormState): Record<string, unknown> | null {
  const options: Record<string, unknown> = {}
  if (form.required) options.required = true
  if (form.defaultValue.trim()) options.default = form.defaultValue.trim()
  if (form.colType === 'select') options.choices = form.choices
  return Object.keys(options).length > 0 ? options : null
}

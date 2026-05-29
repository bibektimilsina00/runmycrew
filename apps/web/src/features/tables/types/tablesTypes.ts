import { z } from 'zod'

export const DataTableSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string().nullable().optional(),
  row_count: z.number().int().nonnegative(),
  column_count: z.number().int().nonnegative(),
  source: z.string(),
  owner: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type DataTable = z.infer<typeof DataTableSchema>

export const TABLE_COLUMN_TYPES = [
  'text',
  'number',
  'boolean',
  'date',
  'select',
  'url',
  'email',
  'phone',
  'textarea',
] as const

export const TableColumnTypeSchema = z.enum(TABLE_COLUMN_TYPES)
export type TableColumnType = z.infer<typeof TableColumnTypeSchema>

export const TableColumnSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  col_type: TableColumnTypeSchema,
  position: z.number().int(),
  options: z.record(z.string(), z.unknown()).nullable().optional(),
})
export type TableColumn = z.infer<typeof TableColumnSchema>

export const TableRowSchema = z.object({
  id: z.string().uuid(),
  data: z.record(z.string(), z.unknown()),
  position: z.number().int().nullable().optional(),
})
export type TableRow = z.infer<typeof TableRowSchema>

export const TableRowsSchema = z.object({
  columns: z.array(TableColumnSchema),
  rows: z.array(TableRowSchema),
})
export type TableRows = z.infer<typeof TableRowsSchema>

export interface TableCreateRequest {
  name: string
  description?: string | null
}

export interface TableColumnRequest {
  name: string
  col_type: TableColumnType
  options?: Record<string, unknown> | null
}

export interface TableRowRequest {
  data: Record<string, unknown>
}

export type TableFilter = 'all' | 'live' | 'static' | 'archived'
export type TableSort = 'updated_desc' | 'name_asc' | 'rows_desc'

import { z } from 'zod'
import apiClient, { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  DataTableSchema,
  TableColumnSchema,
  TableRowSchema,
  TableRowsSchema,
  type TableColumnRequest,
  type TableCreateRequest,
  type TableRowRequest,
} from '../types/tablesTypes'

const DataTableListSchema = z.array(DataTableSchema)

export const tablesAPI = {
  list: (signal?: AbortSignal) =>
    requestJson(DataTableListSchema, { url: API_ROUTES.TABLES_LIST, method: 'GET', signal }),

  create: (data: TableCreateRequest) =>
    requestJson(DataTableSchema, { url: API_ROUTES.TABLES_LIST, method: 'POST', data }),

  delete: (id: string) =>
    requestJson(z.unknown(), { url: API_ROUTES.TABLE(id), method: 'DELETE' }),

  getRows: (id: string, signal?: AbortSignal) =>
    requestJson(TableRowsSchema, { url: API_ROUTES.TABLE_ROWS(id), method: 'GET', signal }),

  addColumn: (id: string, data: TableColumnRequest) =>
    requestJson(TableColumnSchema, { url: API_ROUTES.TABLE_COLUMNS(id), method: 'POST', data }),

  updateColumn: (tableId: string, columnId: string, data: TableColumnRequest) =>
    requestJson(TableColumnSchema, { url: API_ROUTES.TABLE_COLUMN(tableId, columnId), method: 'PATCH', data }),

  deleteColumn: (tableId: string, columnId: string) =>
    requestJson(z.unknown(), { url: API_ROUTES.TABLE_COLUMN(tableId, columnId), method: 'DELETE' }),

  addRow: (id: string, data: TableRowRequest = { data: {} }) =>
    requestJson(TableRowSchema, { url: API_ROUTES.TABLE_ROWS(id), method: 'POST', data }),

  updateRow: (tableId: string, rowId: string, data: TableRowRequest) =>
    requestJson(TableRowSchema, { url: API_ROUTES.TABLE_ROW(tableId, rowId), method: 'PATCH', data }),

  deleteRow: (tableId: string, rowId: string) =>
    requestJson(z.unknown(), { url: API_ROUTES.TABLE_ROW(tableId, rowId), method: 'DELETE' }),

  importCsv: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const response = await apiClient.post(API_ROUTES.TABLES_IMPORT_CSV, form, {
      headers: { 'Content-Type': undefined },
    })
    return DataTableSchema.parse(response.data)
  },

  importRowsCsv: async (id: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    const response = await apiClient.post(API_ROUTES.TABLE_IMPORT_ROWS_CSV(id), form, {
      headers: { 'Content-Type': undefined },
    })
    return z.object({ imported: z.number().int().nonnegative() }).parse(response.data)
  },

  exportCsvBlob: async (id: string) => {
    const response = await apiClient.get<Blob>(API_ROUTES.TABLE_EXPORT_CSV(id), {
      responseType: 'blob',
    })
    return response.data
  },
}

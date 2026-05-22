import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { tablesAPI } from '../services/tablesAPI'
import type { TableColumnRequest, TableCreateRequest, TableRowRequest } from '../types/tablesTypes'

export const tableKeys = {
  all: ['tables'] as const,
  list: () => [...tableKeys.all, 'list'] as const,
  rows: (id: string) => [...tableKeys.all, 'rows', id] as const,
}

export function useTables() {
  return useQuery({
    queryKey: tableKeys.list(),
    queryFn: ({ signal }) => tablesAPI.list(signal),
    staleTime: 1000 * 30,
  })
}

export function useCreateTable() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TableCreateRequest) => tablesAPI.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: tableKeys.list() }),
  })
}

export function useTableRows(tableId: string | null) {
  return useQuery({
    queryKey: tableId ? tableKeys.rows(tableId) : [...tableKeys.all, 'rows', 'none'],
    queryFn: ({ signal }) => tablesAPI.getRows(tableId as string, signal),
    enabled: Boolean(tableId),
    staleTime: 1000 * 15,
  })
}

export function useImportTableCsv() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => tablesAPI.importCsv(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: tableKeys.list() }),
  })
}

export function useDeleteTable() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => tablesAPI.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: tableKeys.list() }),
  })
}

export function useAddTableColumn(tableId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: TableColumnRequest) => tablesAPI.addColumn(tableId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tableKeys.rows(tableId) })
      qc.invalidateQueries({ queryKey: tableKeys.list() })
    },
  })
}

export function useUpdateTableColumn(tableId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ columnId, data }: { columnId: string; data: TableColumnRequest }) =>
      tablesAPI.updateColumn(tableId, columnId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tableKeys.rows(tableId) })
      qc.invalidateQueries({ queryKey: tableKeys.list() })
    },
  })
}

export function useDeleteTableColumn(tableId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (columnId: string) => tablesAPI.deleteColumn(tableId, columnId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tableKeys.rows(tableId) })
      qc.invalidateQueries({ queryKey: tableKeys.list() })
    },
  })
}

export function useAddTableRow(tableId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data?: TableRowRequest) => tablesAPI.addRow(tableId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tableKeys.rows(tableId) })
      qc.invalidateQueries({ queryKey: tableKeys.list() })
    },
  })
}

export function useUpdateTableRow(tableId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ rowId, data }: { rowId: string; data: TableRowRequest }) =>
      tablesAPI.updateRow(tableId, rowId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: tableKeys.rows(tableId) }),
  })
}

export function useDeleteTableRow(tableId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (rowId: string) => tablesAPI.deleteRow(tableId, rowId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tableKeys.rows(tableId) })
      qc.invalidateQueries({ queryKey: tableKeys.list() })
    },
  })
}

export function useImportTableRowsCsv(tableId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => tablesAPI.importRowsCsv(tableId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: tableKeys.rows(tableId) })
      qc.invalidateQueries({ queryKey: tableKeys.list() })
    },
  })
}

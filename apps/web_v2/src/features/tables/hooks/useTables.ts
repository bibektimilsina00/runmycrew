import { useState, useEffect } from 'react'
import type { DataTable } from '../types/tablesTypes'
import { tablesAPI } from '../services/tablesAPI'

export function useTables() {
  const [items, setItems] = useState<DataTable[]>([])
  useEffect(() => { tablesAPI.getAll().then(setItems) }, [])
  return { items }
}

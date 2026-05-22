import { useState, useEffect } from 'react'
import type { Variable } from '../types/variablesTypes'
import { variablesAPI } from '../services/variablesAPI'

export function useVariables() {
  const [items, setItems] = useState<Variable[]>([])
  useEffect(() => { variablesAPI.getAll().then(setItems) }, [])
  return { items }
}

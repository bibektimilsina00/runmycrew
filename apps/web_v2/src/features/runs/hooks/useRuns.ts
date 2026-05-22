import { useState, useEffect } from 'react'
import type { Run } from '../types/runsTypes'
import { runsAPI } from '../services/runsAPI'

export function useRuns() {
  const [items, setItems] = useState<Run[]>([])
  useEffect(() => { runsAPI.getAll().then(setItems) }, [])
  return { items }
}

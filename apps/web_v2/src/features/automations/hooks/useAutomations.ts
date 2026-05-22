import { useState, useEffect } from 'react'
import type { Automation } from '../types/automationsTypes'
import { automationsAPI } from '../services/automationsAPI'

export function useAutomations() {
  const [items, setItems] = useState<Automation[]>([])
  useEffect(() => { automationsAPI.getAll().then(setItems) }, [])
  return { items }
}

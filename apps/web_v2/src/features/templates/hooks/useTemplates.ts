import { useState, useEffect } from 'react'
import type { Template } from '../types/templatesTypes'
import { templatesAPI } from '../services/templatesAPI'

export function useTemplates() {
  const [items, setItems] = useState<Template[]>([])
  useEffect(() => { templatesAPI.getAll().then(setItems) }, [])
  return { items }
}

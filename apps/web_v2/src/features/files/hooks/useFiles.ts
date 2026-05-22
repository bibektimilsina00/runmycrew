import { useState, useEffect } from 'react'
import type { FileItem } from '../types/filesTypes'
import { filesAPI } from '../services/filesAPI'

export function useFiles() {
  const [items, setItems] = useState<FileItem[]>([])
  useEffect(() => { filesAPI.getAll().then(setItems) }, [])
  return { items }
}

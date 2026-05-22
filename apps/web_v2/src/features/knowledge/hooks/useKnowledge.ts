import { useState, useEffect } from 'react'
import type { KnowledgeSource } from '../types/knowledgeTypes'
import { knowledgeAPI } from '../services/knowledgeAPI'

export function useKnowledge() {
  const [items, setItems] = useState<KnowledgeSource[]>([])
  useEffect(() => { knowledgeAPI.getAll().then(setItems) }, [])
  return { items }
}

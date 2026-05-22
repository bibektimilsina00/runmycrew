import { useState, useEffect } from 'react'
import type { Connection } from '../types/connectionsTypes'
import { connectionsAPI } from '../services/connectionsAPI'

export function useConnections() {
  const [items, setItems] = useState<Connection[]>([])
  useEffect(() => { connectionsAPI.getAll().then(setItems) }, [])
  return { items }
}

import { useState, useEffect } from 'react'
import type { Schedule } from '../types/schedulesTypes'
import { schedulesAPI } from '../services/schedulesAPI'

export function useSchedules() {
  const [items, setItems] = useState<Schedule[]>([])
  useEffect(() => { schedulesAPI.getAll().then(setItems) }, [])
  return { items }
}

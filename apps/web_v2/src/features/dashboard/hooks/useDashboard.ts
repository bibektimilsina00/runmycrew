import { useState, useEffect } from 'react'
import { dashboardAPI } from '../services/dashboardAPI'
import type { RunItem, ConnectionItem, ScheduleItem, DashboardStats } from '../types/dashboardTypes'

export function useDashboard() {
  const [runs, setRuns] = useState<RunItem[]>([])
  const [connections, setConnections] = useState<ConnectionItem[]>([])
  const [schedules, setSchedules] = useState<ScheduleItem[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)

  useEffect(() => {
    dashboardAPI.getRuns().then(setRuns)
    dashboardAPI.getConnections().then(setConnections)
    dashboardAPI.getSchedules().then(setSchedules)
    dashboardAPI.getStats().then(setStats)
  }, [])

  return { runs, connections, schedules, stats }
}

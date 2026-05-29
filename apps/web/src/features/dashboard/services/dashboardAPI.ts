import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'

export const DashboardStatSchema = z.object({
  label:     z.string(),
  value:     z.string(),
  unit:      z.string(),
  delta:     z.string(),
  delta_dir: z.enum(['up', 'down', 'flat']),
  spark:     z.array(z.number()),
})

export const DashboardRunSchema = z.object({
  id:       z.string(),
  status:   z.enum(['ok', 'run', 'err', 'warn']),
  name:     z.string(),
  trigger:  z.string(),
  duration: z.string(),
  ago:      z.string(),
})

export const DashboardScheduleSchema = z.object({
  workflow_id: z.string(),
  name:        z.string(),
  time:        z.string(),
  sub:         z.string(),
  next_iso:    z.string(),
})

export const DashboardConnectionSchema = z.object({
  id:    z.string(),
  name:  z.string(),
  type:  z.string(),
  state: z.enum(['ok', 'warn', 'err']),
})

export const DashboardStatsSchema = z.object({
  stats:       z.array(DashboardStatSchema),
  recent_runs: z.array(DashboardRunSchema),
  schedules:   z.array(DashboardScheduleSchema),
  connections: z.array(DashboardConnectionSchema),
  total_today: z.number(),
})

export type DashboardStats      = z.infer<typeof DashboardStatsSchema>
export type DashboardStat       = z.infer<typeof DashboardStatSchema>
export type DashboardRun        = z.infer<typeof DashboardRunSchema>
export type DashboardSchedule   = z.infer<typeof DashboardScheduleSchema>
export type DashboardConnection = z.infer<typeof DashboardConnectionSchema>

export const dashboardAPI = {
  getStats: (signal?: AbortSignal) =>
    requestJson(DashboardStatsSchema, { url: API_ROUTES.DASHBOARD_STATS, method: 'GET', signal }),
}

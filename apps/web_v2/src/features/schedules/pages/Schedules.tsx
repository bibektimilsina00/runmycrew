import { Icons } from '@/shared/components/icons'
import { useSchedules } from '../hooks/useSchedules'
import { ScheduleList } from '../components/ScheduleList'

export function Schedules() {
  const { items } = useSchedules()

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow"><span className="dot" />6 schedules · timezone America/New_York</span>
          <h1>Schedules</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Clock /> Timezone</button>
          <button className="btn btn-primary"><Icons.Plus /> New schedule</button>
        </div>
      </div>

      <ScheduleList items={items} />
    </div>
  )
}

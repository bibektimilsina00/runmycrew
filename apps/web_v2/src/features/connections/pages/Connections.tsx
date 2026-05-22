import { Icons } from '@/shared/components/icons'
import { useConnections } from '../hooks/useConnections'
import { ConnectionGrid } from '../components/ConnectionGrid'

export function Connections() {
  const { items } = useConnections()

  return (
    <div className="view-body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · 18 active</span>
          <h1>Connections</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icons.Doc /> Audit log</button>
          <button className="btn btn-primary"><Icons.Plus /> Connect app</button>
        </div>
      </div>

      <ConnectionGrid items={items} />
    </div>
  )
}

import { Terminal } from 'lucide-react'
import { Empty } from '@/shared/components'

export function LogsPanel() {
  return (
    <Empty
      icon={<Terminal />}
      title="No run logs"
      description="Run the workflow to see execution logs here."
      className="h-full"
    />
  )
}

import type { Node } from 'reactflow'
import type { EditorTab } from '../../stores/editorLayoutStore'
import { CopilotPanel } from '../right-panel/panels/CopilotPanel'
import { NodeLibraryPanel } from '../right-panel/panels/NodeLibraryPanel'
import { TestPanel } from '../right-panel/panels/TestPanel'
import { LogsPanel } from '../right-panel/panels/LogsPanel'
import { EditorInspector } from '../inspector/EditorInspector'

interface Props {
  tab: EditorTab
  nodes: Node[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
  onRun: () => void
  isRunning: boolean
}

export function PanelBody({ tab, nodes, updateNodeData, onRun, isRunning }: Props) {
  switch (tab) {
    case 'copilot': return <CopilotPanel />
    case 'library': return <NodeLibraryPanel />
    case 'config':  return <EditorInspector nodes={nodes} updateNodeData={updateNodeData} className="h-full" />
    case 'logs':    return <LogsPanel />
    case 'test':    return <TestPanel onRun={onRun} isRunning={isRunning} />
    default:        return null
  }
}

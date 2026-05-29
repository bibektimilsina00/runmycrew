import { SlidersHorizontal, Library, FlaskConical, Sparkles } from 'lucide-react'
import type { Node } from 'reactflow'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../stores/workflowEditorStore'
import { EditorInspector } from '../inspector/EditorInspector'
import { EditorActionBar } from './EditorActionBar'
import { CopilotPanel } from './panels/CopilotPanel'
import { NodeLibraryPanel } from './panels/NodeLibraryPanel'
import { TestPanel } from './panels/TestPanel'

interface EditorRightPanelProps {
  nodes: Node[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
  onRun: () => void
  isRunning: boolean
  className?: string
}

type Tab = 'copilot' | 'config' | 'library' | 'test'

const TABS: { id: Tab; label: string; Icon: React.FC<{ className?: string }> }[] = [
  { id: 'copilot',  label: 'Copilot',   Icon: ({ className }) => <Sparkles className={className} /> },
  { id: 'library',  label: 'Library',   Icon: ({ className }) => <Library className={className} /> },
  { id: 'config',   label: 'Inspector', Icon: ({ className }) => <SlidersHorizontal className={className} /> },
  { id: 'test',     label: 'Test',      Icon: ({ className }) => <FlaskConical className={className} /> },
]

export function EditorRightPanel({
  nodes,
  updateNodeData,
  onRun,
  isRunning,
  className,
}: EditorRightPanelProps) {
  const activeTab = useWorkflowEditorStore(s => s.inspectorTab) as Tab
  const setTab = useWorkflowEditorStore(s => s.setInspectorTab)

  return (
    <aside
      className={cn(
        'flex h-full w-[360px] shrink-0 flex-col overflow-hidden border-l border-[var(--border-faint)] bg-[var(--bg-2)]',
        className,
      )}
    >
      {/* Action bar — three-dots, chat, deploy, run */}
      <EditorActionBar onRun={onRun} isRunning={isRunning} />

      {/* Tab row */}
      <nav className="flex shrink-0 items-stretch overflow-x-auto border-b border-[var(--border-faint)] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id as Parameters<typeof setTab>[0])}
            className={cn(
              'relative flex shrink-0 items-center gap-1.5 px-3 py-2.5 text-[12px] font-medium leading-none whitespace-nowrap transition-colors duration-100',
              activeTab === id
                ? 'text-[var(--text)] [&_svg]:text-[var(--text)]'
                : 'text-[var(--text-mute)] hover:text-[var(--text)] [&_svg]:text-[var(--text-faint)] hover:[&_svg]:text-[var(--text-mute)]',
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
            {activeTab === id && (
              <span className="absolute bottom-[-1px] left-2 right-2 h-[2px] rounded-t-[2px] bg-[var(--text)]" />
            )}
          </button>
        ))}
      </nav>

      {/* Panel body */}
      <div className="min-h-0 flex-1 overflow-hidden">
        {activeTab === 'copilot'  && <CopilotPanel />}
        {activeTab === 'config'   && <EditorInspector nodes={nodes} updateNodeData={updateNodeData} className="h-full" />}
        {activeTab === 'library'  && <NodeLibraryPanel />}
        {activeTab === 'test'     && <TestPanel onRun={onRun} isRunning={isRunning} />}
      </div>
    </aside>
  )
}

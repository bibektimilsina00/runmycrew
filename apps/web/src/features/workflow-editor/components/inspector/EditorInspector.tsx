import { SlidersHorizontal, ChevronDown } from 'lucide-react'
import type { Node } from 'reactflow'
import { Empty } from '@/shared/components'
import { cn } from '@/lib/cn'
import { useInspectorNode } from './hooks/use-inspector-node'
import { InspectorHeader } from './components/inspector-header'
import { PropertyGroupList } from './components/property-group-list'
import { OutputSchemaSection } from './components/output-schema-section'

interface EditorInspectorProps {
  nodes: Node[]
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void
  className?: string
}

export function EditorInspector({ nodes, updateNodeData, className }: EditorInspectorProps) {
  const {
    selectedNode,
    definition,
    properties,
    basicGroups,
    advancedGroups,
    showAdvanced,
    toggleAdvanced,
    updateProperty,
    updateLabel,
    closeInspector,
  } = useInspectorNode({ nodes, updateNodeData })

  return (
    <aside
      className={cn(
        'flex h-full w-full flex-col overflow-hidden bg-[var(--bg-2)]',
        className,
      )}
    >
      {!selectedNode || !definition ? (
        <Empty
          icon={<SlidersHorizontal />}
          title="No node selected"
          description="Select a workflow node to edit its dynamic properties."
          className="h-full"
        />
      ) : (
        <>
          <InspectorHeader
            nodeId={selectedNode.id}
            label={(selectedNode.data?.label as string | undefined) || definition.name}
            definition={definition}
            onLabelChange={updateLabel}
            onClose={closeInspector}
          />

          {/* Scrollable body */}
          <div className="min-h-0 flex-1 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {basicGroups.length === 0 && advancedGroups.length === 0 ? (
              <Empty
                title="No configurable fields"
                description="This node does not expose editable properties."
                className="h-full"
              />
            ) : (
              <div className="flex flex-col gap-4 p-4 pb-6">
                {/* Basic fields — no header, no collapsible */}
                <PropertyGroupList
                  groups={basicGroups}
                  definition={definition}
                  properties={properties}
                  onPropertyChange={updateProperty}
                />

                {/* Advanced toggle — v1 dashed divider style */}
                {advancedGroups.length > 0 && (
                  <div className="flex flex-col gap-4">
                    <button
                      type="button"
                      onClick={toggleAdvanced}
                      className="flex items-center gap-3 group"
                    >
                      <div className="h-px flex-1 border-b border-dashed border-[var(--border-faint)]" />
                      <span className="flex items-center gap-1.5 text-[12px] font-semibold text-[var(--text-mute)] transition-colors group-hover:text-[var(--text)]">
                        {showAdvanced ? 'Hide advanced' : 'Show advanced'}
                        <ChevronDown
                          className={cn('h-3.5 w-3.5 transition-transform duration-200', showAdvanced && 'rotate-180')}
                        />
                      </span>
                      <div className="h-px flex-1 border-b border-dashed border-[var(--border-faint)]" />
                    </button>

                    {showAdvanced && (
                      <div className="flex flex-col gap-4">
                        <PropertyGroupList
                          groups={advancedGroups}
                          definition={definition}
                          properties={properties}
                          onPropertyChange={updateProperty}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Output schema — pinned footer, collapsible */}
          <OutputSchemaSection nodeId={selectedNode.id} outputs={definition.outputsSchema} />
        </>
      )}
    </aside>
  )
}

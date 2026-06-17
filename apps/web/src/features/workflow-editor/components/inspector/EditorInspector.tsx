import { SlidersHorizontal, ChevronDown } from 'lucide-react'
import type { Node } from 'reactflow'
import { Empty } from '@/shared/components'
import { cn } from '@/lib/cn'
import { useInspectorNode } from './hooks/use-inspector-node'
import { InspectorHeader } from './components/inspector-header'
import { PropertyGroupList } from './components/property-group-list'
import { TriggerFixtureChip } from './components/trigger-fixture-chip'
import { UpstreamConnectionsSection } from './components/upstream-connections-section'

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
    updateProperties,
    updateLabel,
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
            label={(selectedNode.data?.label as string | undefined) || definition.name}
            definition={definition}
            onLabelChange={updateLabel}
          />

          {definition.category === 'trigger' && (
            <TriggerFixtureChip nodeId={selectedNode.id} />
          )}

          {/* Scrollable body */}
          <div className="min-h-0 flex-1 overflow-y-auto">
            {basicGroups.length === 0 && advancedGroups.length === 0 ? (
              <Empty
                title="No configurable fields"
                description="This node does not expose editable properties."
                className="h-full"
              />
            ) : (
              <div className="flex flex-col gap-[15px] p-4 pb-6">
                <div className="text-[10.5px] font-semibold tracking-[0.07em] text-[var(--text-dim)] uppercase">
                  Configuration
                </div>
                <PropertyGroupList
                  groups={basicGroups}
                  definition={definition}
                  properties={properties}
                  onPropertyChange={updateProperty}
                  onPropertiesChange={updateProperties}
                />

                {advancedGroups.length > 0 && (
                  <div className="flex flex-col gap-[14px]">
                    <button
                      type="button"
                      onClick={toggleAdvanced}
                      className="flex items-center gap-[10px] group pt-[2px]"
                    >
                      <span className="h-px flex-1 bg-[var(--border-faint)]" />
                      <span className="inline-flex items-center gap-[6px] text-[12px] font-semibold text-[var(--text-mute)] transition-colors group-hover:text-[var(--text)]">
                        {showAdvanced ? 'Hide advanced' : 'Show advanced'}
                        <ChevronDown
                          className={cn('h-[13px] w-[13px] transition-transform duration-200', showAdvanced && 'rotate-180')}
                        />
                      </span>
                      <span className="h-px flex-1 bg-[var(--border-faint)]" />
                    </button>

                    {showAdvanced && (
                      <PropertyGroupList
                        groups={advancedGroups}
                        definition={definition}
                        properties={properties}
                        onPropertyChange={updateProperty}
                        onPropertiesChange={updateProperties}
                      />
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          <UpstreamConnectionsSection nodeId={selectedNode.id} />
        </>
      )}
    </aside>
  )
}

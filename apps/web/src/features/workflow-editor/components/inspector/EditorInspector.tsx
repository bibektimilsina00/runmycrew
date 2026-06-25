import { SlidersHorizontal, ChevronDown } from 'lucide-react'
import type { Node } from 'reactflow'
import { Empty } from '@/shared/components'
import { cn } from '@/lib/cn'
import { useInspectorNode } from './hooks/use-inspector-node'
import { InspectorHeader } from './components/inspector-header'
import { PropertyGroupList } from './components/property-group-list'
import { TriggerFixtureChip } from './components/trigger-fixture-chip'
import { UpstreamConnectionsSection } from './components/upstream-connections-section'
import { PeerTypingIndicator, useCollaborationSenders } from '../../collaboration'
import { useEffect } from 'react'

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

  // Broadcast which node *we* have open in the inspector so peers see
  // an "is editing" badge on their copy of the same node. Clears on
  // deselect or unmount so we never leave a stale typing flag set.
  const { sendTyping } = useCollaborationSenders()
  useEffect(() => {
    sendTyping(selectedNode?.id ?? null)
    return () => sendTyping(null)
  }, [selectedNode?.id, sendTyping])

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

          <div className="px-4 pt-2">
            <PeerTypingIndicator nodeId={selectedNode.id} />
          </div>

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
              <div className="flex flex-col gap-[16px] p-4 pb-6">
                <PropertyGroupList
                  groups={basicGroups}
                  definition={definition}
                  properties={properties}
                  onPropertyChange={updateProperty}
                  onPropertiesChange={updateProperties}
                />

                {advancedGroups.length > 0 && (
                  <div className="flex flex-col gap-3 mt-1 border-t border-[var(--border-faint)] pt-3">
                    <button
                      type="button"
                      onClick={toggleAdvanced}
                      className="flex items-center justify-between w-full py-1 text-[10.5px] font-bold uppercase tracking-[0.08em] text-[var(--text-dim)] hover:text-[var(--text)] transition-colors"
                    >
                      <span>Advanced Settings</span>
                      <ChevronDown
                        className={cn(
                          "h-3.5 w-3.5 text-[var(--text-faint)] transition-transform duration-150",
                          showAdvanced && "rotate-180"
                        )}
                      />
                    </button>

                    {showAdvanced && (
                      <div className="animate-in fade-in slide-in-from-top-1 duration-150">
                        <PropertyGroupList
                          groups={advancedGroups}
                          definition={definition}
                          properties={properties}
                          onPropertyChange={updateProperty}
                          onPropertiesChange={updateProperties}
                        />
                      </div>
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

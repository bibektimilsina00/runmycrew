import type { NodeDefinition, NodeProperty } from '../../../types/editorTypes'
import type { InspectorPropertyGroup } from '../utils/inspector-visibility'
import { PropertyField } from '../fields/PropertyField'

interface PropertyGroupListProps {
  groups: InspectorPropertyGroup[]
  definition: NodeDefinition
  properties: Record<string, unknown>
  onPropertyChange: (name: string, value: unknown) => void
  onPropertiesChange?: (patch: Record<string, unknown>) => void
}

export function PropertyGroupList({
  groups,
  definition,
  properties,
  onPropertyChange,
  onPropertiesChange,
}: PropertyGroupListProps) {
  // Single group ('Settings' default bucket) → no header. Multiple groups →
  // render each with a small label so the user can see structure (e.g.
  // "Connection" / "Body" / "Headers" on the HTTP node).
  const showHeaders = groups.length > 1

  return (
    <>
      {groups.map(group => (
        <section key={group.name} className="flex flex-col gap-3">
          {showHeaders && (
            <div className="flex items-center gap-[10px]">
              <span className="text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[var(--text-dim)]">
                {group.name}
              </span>
              <div className="h-px flex-1 bg-[var(--border-faint)]" />
            </div>
          )}
          {group.properties.map(prop => (
            <PropertyFieldSlot
              key={prop.name}
              prop={prop}
              definition={definition}
              properties={properties}
              onPropertyChange={onPropertyChange}
              onPropertiesChange={onPropertiesChange}
            />
          ))}
        </section>
      ))}
    </>
  )
}

interface SlotProps {
  prop: NodeProperty
  definition: NodeDefinition
  properties: Record<string, unknown>
  onPropertyChange: (name: string, value: unknown) => void
  onPropertiesChange?: (patch: Record<string, unknown>) => void
}

function PropertyFieldSlot({
  prop,
  definition,
  properties,
  onPropertyChange,
  onPropertiesChange,
}: SlotProps) {
  const value = properties[prop.name] ?? prop.default
  return (
    <PropertyField
      prop={prop}
      definition={definition}
      properties={properties}
      value={value}
      onChange={v => onPropertyChange(prop.name, v)}
      onPropertiesChange={onPropertiesChange}
      defaultValue={prop.default}
      onReset={prop.default !== undefined ? () => onPropertyChange(prop.name, prop.default) : undefined}
    />
  )
}

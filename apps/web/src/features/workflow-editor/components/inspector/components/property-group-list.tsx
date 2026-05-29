import type { NodeDefinition } from '../../../types/editorTypes'
import type { InspectorPropertyGroup } from '../utils/inspector-visibility'
import { PropertyField } from './property-field'

interface PropertyGroupListProps {
  groups: InspectorPropertyGroup[]
  definition: NodeDefinition
  properties: Record<string, unknown>
  onPropertyChange: (name: string, value: unknown) => void
}

export function PropertyGroupList({ groups, definition, properties, onPropertyChange }: PropertyGroupListProps) {
  return (
    <>
      {groups.flatMap(group =>
        group.properties.map(prop => (
          <PropertyField
            key={prop.name}
            prop={prop}
            definition={definition}
            properties={properties}
            value={properties[prop.name] ?? prop.default}
            onChange={value => onPropertyChange(prop.name, value)}
          />
        )),
      )}
    </>
  )
}

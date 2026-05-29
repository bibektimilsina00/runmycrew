import type { NodeDefinition, NodeProperty } from '../../../types/editorTypes'
import { PropertyField as FieldSystemPropertyField } from '../fields/PropertyField'

interface PropertyFieldProps {
  prop: NodeProperty
  definition: NodeDefinition
  properties: Record<string, unknown>
  value: unknown
  onChange: (value: unknown) => void
}

export function PropertyField(props: PropertyFieldProps) {
  return <FieldSystemPropertyField {...props} />
}

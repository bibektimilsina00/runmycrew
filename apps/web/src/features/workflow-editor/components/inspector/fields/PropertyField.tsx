import type { NodeDefinition, NodeProperty } from '../../../types/editorTypes'
import { FieldWrapper } from './FieldWrapper'
import { ExpressionInput } from './ExpressionInput'
import { FIELD_RENDERERS, FallbackRenderer } from './index'

export interface PropertyFieldProps {
  prop: NodeProperty
  definition: NodeDefinition
  properties: Record<string, unknown>
  value: unknown
  onChange: (value: unknown) => void
}

export function PropertyField({ prop, definition, properties, value, onChange }: PropertyFieldProps) {
  const modes = (properties._modes as Record<string, string> | undefined) ?? {}
  const isExpression = modes[prop.name] === 'dynamic'

  const onToggleExpression = () => {
    const next = isExpression ? 'manual' : 'dynamic'
    const newModes = { ...modes, [prop.name]: next }
    onChange({ __modes_update: true, modes: newModes })
  }

  const Renderer = FIELD_RENDERERS[prop.type as keyof typeof FIELD_RENDERERS] ?? FallbackRenderer

  return (
    <FieldWrapper prop={prop} isExpression={isExpression} onToggleExpression={onToggleExpression}>
      {isExpression ? (
        <ExpressionInput value={value} onChange={onChange} />
      ) : (
        <Renderer
          prop={prop}
          definition={definition}
          properties={properties}
          value={value}
          onChange={onChange}
        />
      )}
    </FieldWrapper>
  )
}

import type { NodeDefinition, NodeProperty } from '../../../types/editorTypes'
import { FieldWrapper } from './FieldWrapper'
import { FIELD_RENDERERS, FallbackRenderer } from './index'

export interface PropertyFieldProps {
  prop: NodeProperty
  definition: NodeDefinition
  properties: Record<string, unknown>
  value: unknown
  onChange: (value: unknown) => void
  /** Multi-field patch — used by renderers that derive sibling fields
   *  (e.g. MediaRenderer deriving `kind` from the picked file's mime). */
  onPropertiesChange?: (patch: Record<string, unknown>) => void

  /** Render the field as read-only (greys out + disables inputs). */
  readOnly?: boolean

  /** When set, the field wrapper renders a small reset-to-default button. */
  defaultValue?: unknown
  onReset?: () => void
}

export function PropertyField({
  prop,
  definition,
  properties,
  value,
  onChange,
  onPropertiesChange,
  readOnly,
  defaultValue,
  onReset,
}: PropertyFieldProps) {
  const Renderer = FIELD_RENDERERS[prop.type as keyof typeof FIELD_RENDERERS] ?? FallbackRenderer

  return (
    <FieldWrapper
      prop={prop}
      canReset={defaultValue !== undefined && !sameValue(value, defaultValue)}
      onReset={onReset}
    >
      <Renderer
        prop={prop}
        definition={definition}
        properties={properties}
        value={value}
        onChange={onChange}
        onPropertiesChange={onPropertiesChange}
        disabled={readOnly}
      />
    </FieldWrapper>
  )
}

function sameValue(a: unknown, b: unknown): boolean {
  if (a === b) return true
  if (a == null && b == null) return true
  // Loose compare for primitives that round-trip through strings.
  if (typeof a !== 'object' && typeof b !== 'object') return String(a) === String(b)
  try { return JSON.stringify(a) === JSON.stringify(b) } catch { return false }
}

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

  /** Manual = native renderer; dynamic = expression input (`{{...}}`). */
  mode?: 'manual' | 'dynamic'
  onModeChange?: (mode: 'manual' | 'dynamic') => void

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
  mode = 'manual',
  onModeChange,
  readOnly,
  defaultValue,
  onReset,
}: PropertyFieldProps) {
  const isExpression = mode === 'dynamic'
  const Renderer = FIELD_RENDERERS[prop.type as keyof typeof FIELD_RENDERERS] ?? FallbackRenderer

  // A "list" only exists when the field actually picks from one — either an
  // options renderer (with static options or a loadOptions endpoint) or a
  // credential picker. Plain text / number / code fields get a single `fx`
  // toggle instead of the List | fx pill.
  const hasList =
    prop.type === 'options' ||
    prop.type === 'multi-options' ||
    prop.type === 'credential' ||
    !!prop.loadOptions ||
    (prop.options?.length ?? 0) > 0

  return (
    <FieldWrapper
      prop={prop}
      isExpression={isExpression}
      onToggleExpression={onModeChange ? () => onModeChange(isExpression ? 'manual' : 'dynamic') : undefined}
      hasList={hasList}
      canReset={defaultValue !== undefined && !sameValue(value, defaultValue)}
      onReset={onReset}
    >
      {isExpression ? (
        <ExpressionInput value={value} onChange={onChange} />
      ) : (
        <Renderer
          prop={prop}
          definition={definition}
          properties={properties}
          value={value}
          onChange={onChange}
          disabled={readOnly}
        />
      )}
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

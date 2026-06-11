import type { FC } from 'react'
import type { NodeDefinition, NodeProperty } from '../../../types/editorTypes'

/**
 * Shared signature for every field renderer. Renderers may ignore any prop
 * they don't need — TypeScript's structural typing means a narrower signature
 * is assignable to this one without a cast.
 */
export interface RendererProps {
  prop: NodeProperty
  definition: NodeDefinition
  properties: Record<string, unknown>
  value: unknown
  onChange: (value: unknown) => void
  disabled?: boolean
}

export type FieldRenderer = FC<RendererProps>

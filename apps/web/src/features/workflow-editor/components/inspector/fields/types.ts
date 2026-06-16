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
  /** Patch multiple properties in a single write. Set when the renderer
   *  derives sibling fields from its own value (e.g. MediaRenderer auto-
   *  selecting `kind` from a picked file's mime). Renderers that don't
   *  need it can ignore the prop entirely. */
  onPropertiesChange?: (patch: Record<string, unknown>) => void
  disabled?: boolean
}

export type FieldRenderer = FC<RendererProps>

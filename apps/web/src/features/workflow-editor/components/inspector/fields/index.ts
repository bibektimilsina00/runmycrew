import type { FC } from 'react'
import type { NodeDefinition, NodeProperty, NodePropertyType } from '../../../types/editorTypes'

export interface RendererProps {
  prop: NodeProperty
  definition: NodeDefinition
  properties: Record<string, unknown>
  value: unknown
  onChange: (value: unknown) => void
}

export type FieldRenderer = FC<RendererProps>

// Import all renderers
import { StringRenderer } from './renderers/StringRenderer'
import { NumberRenderer } from './renderers/NumberRenderer'
import { BooleanRenderer } from './renderers/BooleanRenderer'
import { OptionsRenderer } from './renderers/OptionsRenderer'
import { CredentialRenderer } from './renderers/CredentialRenderer'
import { CodeRenderer } from './renderers/CodeRenderer'
import { JsonRenderer } from './renderers/JsonRenderer'
import { KeyValueRenderer } from './renderers/KeyValueRenderer'
import { ListRenderer } from './renderers/ListRenderer'
import { MessagesRenderer } from './renderers/MessagesRenderer'
import { CollectionRenderer } from './renderers/CollectionRenderer'
import { ToolSelectorRenderer } from './renderers/ToolSelectorRenderer'
import { SkillSelectorRenderer } from './renderers/SkillSelectorRenderer'

export const FIELD_RENDERERS: Partial<Record<NodePropertyType, FieldRenderer>> = {
  string:             StringRenderer as FieldRenderer,
  number:             NumberRenderer as FieldRenderer,
  boolean:            BooleanRenderer as FieldRenderer,
  options:            OptionsRenderer as FieldRenderer,
  'multi-options':    OptionsRenderer as FieldRenderer,
  credential:         CredentialRenderer as FieldRenderer,
  code:               CodeRenderer as FieldRenderer,
  json:               JsonRenderer as FieldRenderer,
  schema:             JsonRenderer as FieldRenderer,
  'key-value':        KeyValueRenderer as FieldRenderer,
  list:               ListRenderer as FieldRenderer,
  'file-list':        ListRenderer as FieldRenderer,
  messages:           MessagesRenderer as FieldRenderer,
  collection:         CollectionRenderer as FieldRenderer,
  'fixed-collection': CollectionRenderer as FieldRenderer,
  'tool-selector':    ToolSelectorRenderer as FieldRenderer,
  'skill-selector':   SkillSelectorRenderer as FieldRenderer,
}

export { JsonRenderer as FallbackRenderer }

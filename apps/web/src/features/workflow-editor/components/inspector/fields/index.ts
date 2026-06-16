import type { NodePropertyType } from '../../../types/editorTypes'
import type { FieldRenderer } from './types'

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
import { MetaResourceRenderer } from './renderers/MetaResourceRenderer'
import { WATemplateRenderer } from './renderers/WATemplateRenderer'
import { MediaRenderer } from './renderers/MediaRenderer'
import { GmailQueryRenderer } from './renderers/GmailQueryRenderer'
import { GDrivePickerRenderer } from './renderers/GDrivePickerRenderer'
import { GoogleFilePickerRenderer } from './renderers/GoogleFilePickerRenderer'
import { GSheetsTabPickerRenderer } from './renderers/GSheetsTabPickerRenderer'

export type { RendererProps, FieldRenderer } from './types'

export const FIELD_RENDERERS: Partial<Record<NodePropertyType, FieldRenderer>> = {
  string:             StringRenderer,
  number:             NumberRenderer,
  boolean:            BooleanRenderer,
  options:            OptionsRenderer,
  'multi-options':    OptionsRenderer,
  credential:         CredentialRenderer,
  code:               CodeRenderer,
  json:               JsonRenderer,
  schema:             JsonRenderer,
  'key-value':        KeyValueRenderer,
  list:               ListRenderer,
  'file-list':        ListRenderer,
  messages:           MessagesRenderer,
  collection:         CollectionRenderer,
  'fixed-collection': CollectionRenderer,
  'tool-selector':    ToolSelectorRenderer,
  'skill-selector':   SkillSelectorRenderer,
  'meta-resource':    MetaResourceRenderer,
  'wa-template':      WATemplateRenderer,
  media:              MediaRenderer,
  'gmail-query':      GmailQueryRenderer,
  'gdrive-folder':    GDrivePickerRenderer,
  'google-file':      GoogleFilePickerRenderer,
  'gsheet-tab':       GSheetsTabPickerRenderer,
}

export { JsonRenderer as FallbackRenderer }

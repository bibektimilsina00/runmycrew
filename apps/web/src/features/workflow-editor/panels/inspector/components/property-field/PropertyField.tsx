import React from 'react'
import { List, Type, ArrowLeftRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { NodeDefinition, NodeProperty } from '@fuse/node-definitions'
import { usePropertyField } from '@/features/workflow-editor/hooks/use-property-field'
import { useDependsOnGate } from '../../hooks/use-depends-on-gate'
import { toInputValue } from '../../utils/field-helpers'
import type { CanonicalIndex, CanonicalModeOverrides } from '../../visibility'

import { StringInput } from './renderers/StringInput'
import { NumberInput } from './renderers/NumberInput'
import { BooleanInput } from './renderers/BooleanInput'
import { OptionsSelect } from './renderers/OptionsSelect'
import { CodeEditor } from './renderers/CodeEditor'
import { MessagesInput } from './renderers/MessagesInput'
import { KeyValueField } from '../key-value-field'
import { SchemaEditorField } from '../schema-editor-field'
import { CredentialPicker } from '../credential-picker'
import { FileListField } from '../file-list-field'
import { ToolSelectorField } from '../tool-selector-field/ToolSelectorField'
import { SkillSelectorField } from '../skill-selector-field/SkillSelectorField'

export interface PropertyFieldProps {
  prop: NodeProperty
  selectedNode: any
  properties: Record<string, any>
  handlePropertyChange: (name: string, value: any) => void
  onShowPicker: (rect: DOMRect, onSelect: (val: string) => void) => void
  isFirstClickAllowed: (subId?: string) => boolean
  onFirstClickUsed: (subId?: string) => void
  definition: NodeDefinition
  canonicalIndex?: CanonicalIndex
  canonicalModes?: CanonicalModeOverrides
  /** When set, render the basic ↔ advanced swap button for this canonical pair. */
  canonicalToggle?: { mode: 'basic' | 'advanced'; onToggle: () => void }
}

export const PropertyField: React.FC<PropertyFieldProps> = (props) => {
  const {
    prop, handlePropertyChange, onShowPicker, isFirstClickAllowed, onFirstClickUsed,
    definition, properties, canonicalIndex, canonicalModes, canonicalToggle,
  } = props

  const {
    mode, dynamicOptions, isLoadingOptions, currentValue, toggleMode, handleInputInteraction, handleKeyDown, getLabel,
  } = usePropertyField(props)

  const { disabled, tooltip } = useDependsOnGate(prop, properties, canonicalIndex, canonicalModes)

  const onChange = (val: any) => handlePropertyChange(prop.name, val)
  const credentialType =
    prop.credentialType
    || (prop.credentialTypeByField
      ? prop.credentialTypeByField.values?.[properties[prop.credentialTypeByField.field]]
      : undefined)
    || definition?.credentialType

  const renderInput = () => {
    switch (prop.type) {
      case 'string':
        return (
          <StringInput
            prop={prop}
            value={currentValue}
            onChange={onChange}
            mode={mode}
            dynamicOptions={dynamicOptions}
            isLoadingOptions={isLoadingOptions}
            onFocus={handleInputInteraction}
            onClick={handleInputInteraction}
            onKeyDown={handleKeyDown}
          />
        )
      case 'number':
        return (
          <NumberInput
            prop={prop}
            value={currentValue}
            onChange={onChange}
            onFocus={handleInputInteraction}
            onClick={handleInputInteraction}
            onKeyDown={handleKeyDown}
          />
        )
      case 'boolean':
        return <BooleanInput value={!!currentValue} onChange={onChange} />

      case 'options':
        return <OptionsSelect prop={prop} value={currentValue} onChange={onChange} />

      case 'key-value':
        return (
          <KeyValueField
            value={properties[prop.name] || prop.default || {}}
            onChange={onChange}
            onShowPicker={onShowPicker}
            isFirstClickAllowed={isFirstClickAllowed}
            onFirstClickUsed={onFirstClickUsed}
          />
        )
      case 'schema':
        return (
          <SchemaEditorField
            value={properties[prop.name] || prop.default || []}
            onChange={onChange}
          />
        )
      case 'credential':
        return (
          <CredentialPicker
            value={currentValue}
            onChange={onChange}
            credentialType={credentialType}
            placeholder={prop.placeholder}
          />
        )
      case 'file-list':
        return (
          <FileListField
            value={properties[prop.name] || []}
            onChange={onChange}
          />
        )
      case 'tool-selector':
        return (
          <ToolSelectorField
            value={properties[prop.name] || []}
            onChange={onChange}
            disabled={disabled}
          />
        )
      case 'skill-selector':
        return (
          <SkillSelectorField
            value={properties[prop.name] || []}
            onChange={onChange}
            disabled={disabled}
          />
        )
      case 'json':
      case 'list':
        return (
          <CodeEditor
            prop={prop}
            value={currentValue}
            onChange={onChange}
            onShowPicker={onShowPicker}
            isFirstClickAllowed={() => isFirstClickAllowed()}
            onFirstClickUsed={() => onFirstClickUsed()}
          />
        )
      case 'messages':
        return (
          <MessagesInput
            value={currentValue}
            onChange={onChange}
          />
        )
      default:
        return (
          <input
            type={prop.secret ? 'password' : 'text'}
            value={toInputValue(currentValue)}
            onFocus={handleInputInteraction}
            onClick={handleInputInteraction}
            onKeyDown={handleKeyDown}
            onChange={(e) => onChange(e.target.value)}
            placeholder={prop.placeholder || `Enter ${prop.label}`}
            className="w-full bg-surface-editor border border-border rounded-md px-3 h-[36px] text-[13px] text-white placeholder:text-text-placeholder focus:outline-none"
          />
        )
    }
  }

  const content = (
    <div className={cn(
      "flex flex-col gap-1.5 animate-in fade-in slide-in-from-top-1 duration-200",
      disabled && "opacity-50 pointer-events-none select-none",
    )}>
      <div className="flex items-center justify-between mb-1">
        <label className="text-[12px] font-bold text-white">
          {getLabel()}
          {prop.required && <span className="text-red-500 ml-1.5">*</span>}
        </label>
        <div className="flex items-center gap-1">
          {canonicalToggle && (
            <button
              onClick={canonicalToggle.onToggle}
              className="p-1 rounded hover:bg-surface-5 text-text-placeholder hover:text-white transition-all active:scale-95"
              title={canonicalToggle.mode === 'basic' ? 'Switch to advanced input' : 'Switch to simple input'}
            >
              <ArrowLeftRight size={12} />
            </button>
          )}
          {prop.loadOptions && !canonicalToggle && (
            <button
              onClick={toggleMode}
              className="p-1 rounded hover:bg-surface-5 text-text-placeholder hover:text-white transition-all active:scale-95"
              title={mode === 'manual' ? 'Switch to List' : 'Switch to Manual ID'}
            >
              {mode === 'manual' ? <Type size={12} /> : <List size={12} />}
            </button>
          )}
          {prop.type === 'json' && (
            <button className="h-[22px] px-2.5 rounded bg-surface-5 hover:bg-surface-6 text-[11px] font-medium text-white transition-colors">
              Generate
            </button>
          )}
        </div>
      </div>

      {renderInput()}

      {prop.description && (
        <p className="text-[11px] text-[var(--text-muted)] leading-snug mt-0.5">{prop.description}</p>
      )}
    </div>
  )

  if (!disabled) return content

  return (
    <div title={tooltip ?? undefined}>
      {content}
      {tooltip && <p className="mt-1 text-[11px] text-[var(--text-muted)] italic">{tooltip}</p>}
    </div>
  )
}

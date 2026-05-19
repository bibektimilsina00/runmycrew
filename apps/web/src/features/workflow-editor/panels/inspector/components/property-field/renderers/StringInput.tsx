import React from 'react'
import { RefreshCw } from 'lucide-react'
import type { NodeProperty } from '@fuse/node-definitions'
import { CustomSelect } from '../../custom-select'
import { toInputValue } from '../../../utils/field-helpers'
import {
  hasInterpolationDragData,
  insertInterpolationAtSelection,
  readInterpolationDragData,
} from '@/features/workflow-editor/utils/interpolation'

interface StringInputProps {
  prop: NodeProperty
  value: any
  onChange: (val: any) => void
  mode: 'manual' | 'dynamic'
  dynamicOptions: { label: string; value: any }[]
  isLoadingOptions: boolean
  onFocus: (e: React.FocusEvent<HTMLInputElement>) => void
  onClick: (e: React.MouseEvent<HTMLInputElement>) => void
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void
}

export const StringInput: React.FC<StringInputProps> = ({
  prop, value, onChange, mode, dynamicOptions, isLoadingOptions, onFocus, onClick, onKeyDown,
}) => {
  if (mode === 'dynamic' && prop.loadOptions) {
    return (
      <div className="relative">
        <CustomSelect
          value={value}
          options={dynamicOptions}
          onChange={onChange}
          placeholder={isLoadingOptions ? 'Loading...' : prop.placeholder || `Select ${prop.label}`}
        />
        {isLoadingOptions && (
          <div className="absolute right-9 top-1/2 -translate-y-1/2">
            <RefreshCw size={12} className="text-text-placeholder animate-spin" />
          </div>
        )}
      </div>
    )
  }

  return (
    <input
      type={prop.secret ? 'password' : 'text'}
      value={toInputValue(value)}
      onFocus={onFocus}
      onClick={onClick}
      onKeyDown={onKeyDown}
      onChange={(e) => onChange(e.target.value)}
      onDragOver={(e) => {
        if (!hasInterpolationDragData(e)) return
        e.preventDefault()
        e.dataTransfer.dropEffect = 'copy'
      }}
      onDrop={(e) => {
        const interpolation = readInterpolationDragData(e)
        if (!interpolation) return

        e.preventDefault()
        const target = e.currentTarget
        onChange(insertInterpolationAtSelection(
          target.value,
          interpolation,
          target.selectionStart ?? target.value.length,
          target.selectionEnd ?? target.value.length,
        ))
      }}
      placeholder={prop.placeholder || `Enter ${prop.label}`}
      className="w-full bg-surface-editor border border-border rounded-md px-3 h-[36px] text-[13px] text-white placeholder:text-text-placeholder focus:outline-none"
    />
  )
}

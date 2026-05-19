import React, { useState } from 'react'
import { cn } from '@/lib/utils'
import { Trash2 } from 'lucide-react'
import {
  hasInterpolationDragData,
  insertInterpolationAtSelection,
  readInterpolationDragData,
} from '@/features/workflow-editor/utils/interpolation'

export const KeyValueField = ({ 
  value, 
  onChange,
  onShowPicker,
  isFirstClickAllowed,
  onFirstClickUsed
}: { 
  value: any, 
  onChange: (val: any) => void,
  onShowPicker?: (rect: DOMRect, onSelect: (val: string) => void) => void,
  isFirstClickAllowed?: (subId?: string) => boolean,
  onFirstClickUsed?: (subId?: string) => void
}) => {
  const [pairs, setPairs] = useState<{key: string, value: string}[]>(() => {
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      const entries = Object.entries(value).map(([k, v]) => ({ key: k, value: String(v) }))
      return entries.length > 0 ? [...entries, { key: '', value: '' }] : [{ key: '', value: '' }, { key: '', value: '' }]
    }
    return [{ key: '', value: '' }, { key: '', value: '' }]
  })

  const syncToParent = (currentPairs: {key: string, value: string}[]) => {
    const newObj: Record<string, string> = {}
    currentPairs.forEach(p => {
      if (p.key.trim()) {
        newObj[p.key.trim()] = p.value
      }
    })
    onChange(newObj)
  }

  const handleChange = (index: number, field: 'key' | 'value', val: string) => {
    const newPairs = [...pairs]
    newPairs[index][field] = val
    
    // Auto-add new empty row if the last row is being typed into
    const isLast = index === newPairs.length - 1
    if (isLast && (newPairs[index].key || newPairs[index].value)) {
      newPairs.push({ key: '', value: '' })
    }

    setPairs(newPairs)
    syncToParent(newPairs)
  }

  const handleDelete = (index: number) => {
    if (pairs.length === 1) return // Keep at least one row
    const newPairs = pairs.filter((_, i) => i !== index)
    setPairs(newPairs)
    syncToParent(newPairs)
  }

  const handleDragOver = (event: React.DragEvent<HTMLInputElement>) => {
    if (!hasInterpolationDragData(event)) return
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
  }

  const handleDrop = (
    event: React.DragEvent<HTMLInputElement>,
    index: number,
    field: 'key' | 'value',
  ) => {
    const interpolation = readInterpolationDragData(event)
    if (!interpolation) return

    event.preventDefault()
    const target = event.currentTarget
    handleChange(index, field, insertInterpolationAtSelection(
      target.value,
      interpolation,
      target.selectionStart ?? target.value.length,
      target.selectionEnd ?? target.value.length,
    ))
  }

  return (
    <div className="flex flex-col border border-border rounded-md overflow-hidden bg-surface-editor">
      <div className="flex bg-surface-modal border-b border-border">
        <div className="flex-1 py-1.5 px-2 text-[11px] font-bold text-text-muted">Key</div>
        <div className="w-[1px] bg-surface-5 flex-shrink-0" />
        <div className="flex-1 py-1.5 px-2 text-[11px] font-bold text-text-muted">Value</div>
        <div className="w-8 flex-shrink-0" /> {/* Match delete button width */}
      </div>
      {pairs.map((pair, idx) => {
        const isLast = idx === pairs.length - 1
        const keyId = `key-${idx}`
        const valueId = `value-${idx}`
        
        return (
          <div key={idx} className={cn("flex group", !isLast && "border-b border-border")}>
            <input
              value={pair.key}
              onFocus={e => {
                const target = e.target as HTMLInputElement
                if (isFirstClickAllowed && onShowPicker && onFirstClickUsed && isFirstClickAllowed(keyId)) {
                  const rect = target.getBoundingClientRect()
                  const start = target.selectionStart || 0
                  const end = target.selectionEnd || 0
                  const valueAtTrigger = target.value

                  onShowPicker(rect, (val) => {
                    const textBefore = valueAtTrigger.substring(0, start)
                    const hasTrigger = textBefore.endsWith('{{')
                    const newVal = (hasTrigger ? textBefore.slice(0, -2) : textBefore) + val + valueAtTrigger.substring(end)
                    handleChange(idx, 'key', newVal)
                  })
                  onFirstClickUsed(keyId)
                }
              }}
              onClick={e => {
                const target = e.target as HTMLInputElement
                if (isFirstClickAllowed && onShowPicker && onFirstClickUsed && isFirstClickAllowed(keyId)) {
                  const rect = target.getBoundingClientRect()
                  const start = target.selectionStart || 0
                  const end = target.selectionEnd || 0
                  const valueAtTrigger = target.value

                  onShowPicker(rect, (val) => {
                    const textBefore = valueAtTrigger.substring(0, start)
                    const hasTrigger = textBefore.endsWith('{{')
                    const newVal = (hasTrigger ? textBefore.slice(0, -2) : textBefore) + val + valueAtTrigger.substring(end)
                    handleChange(idx, 'key', newVal)
                  })
                  onFirstClickUsed(keyId)
                }
              }}
              onKeyDown={e => {
                const target = e.target as HTMLInputElement
                if (e.key === '{' && target.value[target.selectionStart! - 1] === '{' && onShowPicker) {
                  const rect = target.getBoundingClientRect()
                  setTimeout(() => {
                    const start = target.selectionStart || 0
                    const end = target.selectionEnd || 0
                    const valueAtTrigger = target.value

                    onShowPicker(rect, (val) => {
                      const textBefore = valueAtTrigger.substring(0, start)
                      const hasTrigger = textBefore.endsWith('{{')
                      const newVal = (hasTrigger ? textBefore.slice(0, -2) : textBefore) + val + valueAtTrigger.substring(end)
                      handleChange(idx, 'key', newVal)
                    })
                  }, 0)
                }
              }}
              onChange={e => handleChange(idx, 'key', e.target.value)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, idx, 'key')}
              placeholder="Key"
              className="flex-1 bg-transparent px-2 py-1.5 text-[12px] text-white focus:outline-none placeholder:text-text-placeholder min-w-0"
            />
            <div className="w-[1px] bg-surface-5 flex-shrink-0" />
            <input
              value={pair.value}
              onFocus={e => {
                const target = e.target as HTMLInputElement
                if (isFirstClickAllowed && onShowPicker && onFirstClickUsed && isFirstClickAllowed(valueId)) {
                  const rect = target.getBoundingClientRect()
                  const start = target.selectionStart || 0
                  const end = target.selectionEnd || 0
                  const valueAtTrigger = target.value

                  onShowPicker(rect, (val) => {
                    const textBefore = valueAtTrigger.substring(0, start)
                    const hasTrigger = textBefore.endsWith('{{')
                    const newVal = (hasTrigger ? textBefore.slice(0, -2) : textBefore) + val + valueAtTrigger.substring(end)
                    handleChange(idx, 'value', newVal)
                  })
                  onFirstClickUsed(valueId)
                }
              }}
              onClick={e => {
                const target = e.target as HTMLInputElement
                if (isFirstClickAllowed && onShowPicker && onFirstClickUsed && isFirstClickAllowed(valueId)) {
                  const rect = target.getBoundingClientRect()
                  const start = target.selectionStart || 0
                  const end = target.selectionEnd || 0
                  const valueAtTrigger = target.value

                  onShowPicker(rect, (val) => {
                    const textBefore = valueAtTrigger.substring(0, start)
                    const hasTrigger = textBefore.endsWith('{{')
                    const newVal = (hasTrigger ? textBefore.slice(0, -2) : textBefore) + val + valueAtTrigger.substring(end)
                    handleChange(idx, 'value', newVal)
                  })
                  onFirstClickUsed(valueId)
                }
              }}
              onKeyDown={e => {
                const target = e.target as HTMLInputElement
                if (e.key === '{' && target.value[target.selectionStart! - 1] === '{' && onShowPicker) {
                  const rect = target.getBoundingClientRect()
                  setTimeout(() => {
                    const start = target.selectionStart || 0
                    const end = target.selectionEnd || 0
                    const valueAtTrigger = target.value

                    onShowPicker(rect, (val) => {
                      const textBefore = valueAtTrigger.substring(0, start)
                      const hasTrigger = textBefore.endsWith('{{')
                      const newVal = (hasTrigger ? textBefore.slice(0, -2) : textBefore) + val + valueAtTrigger.substring(end)
                      handleChange(idx, 'value', newVal)
                    })
                  }, 0)
                }
              }}
              onChange={e => handleChange(idx, 'value', e.target.value)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, idx, 'value')}
              placeholder="Value"
              className="flex-1 bg-transparent px-2 py-1.5 text-[12px] text-white focus:outline-none placeholder:text-text-placeholder min-w-0"
            />
            <div className="w-8 flex-shrink-0 flex items-center justify-center">
              {!isLast && (
                <button
                  onClick={() => handleDelete(idx)}
                  className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-red-500 transition-all p-1 rounded"
                  aria-label="Remove field"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

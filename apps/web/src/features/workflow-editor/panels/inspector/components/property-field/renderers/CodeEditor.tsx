import React from 'react'
import Editor from 'react-simple-code-editor'
import Prism from 'prismjs'
import '@/styles/prism.css'
import type { NodeProperty } from '@fuse/node-definitions'
import { toEditorValue, parseStructuredValue } from '../../../utils/field-helpers'
import {
  hasInterpolationDragData,
  insertInterpolationAtSelection,
  readInterpolationDragData,
} from '@/features/workflow-editor/utils/interpolation'

;(globalThis as any).Prism = Prism

// Load language grammars — interpolation {{}} highlighted in all
const addInterpolation = (lang: any) => {
  if (lang) lang['interpolation'] = { pattern: /\{\{.*?\}\}/g, alias: 'important' }
}
import('prismjs/components/prism-json').then(() => addInterpolation(Prism.languages.json))
import('prismjs/components/prism-python').then(() => addInterpolation(Prism.languages.python))
import('prismjs/components/prism-javascript').then(() => addInterpolation(Prism.languages.javascript))

interface CodeEditorProps {
  prop: NodeProperty
  value: any
  onChange: (val: any) => void
  onShowPicker: (rect: DOMRect, onSelect: (val: string) => void) => void
  isFirstClickAllowed: () => boolean
  onFirstClickUsed: () => void
  language?: string
}

function getHighlighter(language?: string) {
  if (language === 'python') return (code: string) => Prism.highlight(code || '', Prism.languages.python || Prism.languages.plain || {}, 'python')
  if (language === 'javascript') return (code: string) => Prism.highlight(code || '', Prism.languages.javascript || Prism.languages.plain || {}, 'javascript')
  return (code: string) => Prism.highlight(code || '', Prism.languages.json || {}, 'json')
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  prop, value, onChange, onShowPicker, isFirstClickAllowed, onFirstClickUsed, language,
}) => {
  const editorValue = toEditorValue(value, prop.type === 'list' || prop.type === 'code' ? (prop.default ?? '') : prop.default)

  const openPicker = (target: HTMLTextAreaElement) => {
    const rect = target.getBoundingClientRect()
    const start = target.selectionStart || 0
    const end = target.selectionEnd || 0
    const snapshot = target.value
    onShowPicker(rect, (val) => {
      const before = snapshot.substring(0, start)
      const newVal = (before.endsWith('{{') ? before.slice(0, -2) : before) + val + snapshot.substring(end)
      onChange(parseStructuredValue(newVal))
    })
  }

  return (
    <div className="w-full bg-surface-editor rounded-md overflow-hidden transition-all">
      <Editor
        value={editorValue}
        onValueChange={(code) => onChange(parseStructuredValue(code))}
        highlight={getHighlighter(language)}
        padding={12}
        className="prism-editor min-h-[100px] focus:outline-none"
        textareaClassName="focus:outline-none"
        onFocus={(e: any) => {
          if (isFirstClickAllowed()) { openPicker(e.target); onFirstClickUsed() }
        }}
        onClick={(e: any) => {
          if (isFirstClickAllowed()) { openPicker(e.target); onFirstClickUsed() }
        }}
        onKeyDown={(e: any) => {
          const target = e.target as HTMLTextAreaElement
          if (e.key === '{' && target.value[target.selectionStart - 1] === '{') {
            const rect = target.getBoundingClientRect()
            setTimeout(() => {
              const start = target.selectionStart || 0
              const end = target.selectionEnd || 0
              const snapshot = target.value
              onShowPicker(rect, (val) => {
                const before = snapshot.substring(0, start)
                const newVal = (before.endsWith('{{') ? before.slice(0, -2) : before) + val + snapshot.substring(end)
                onChange(parseStructuredValue(newVal))
              })
            }, 0)
          }
        }}
        onDragOver={(e) => {
          if (!hasInterpolationDragData(e)) return
          e.preventDefault()
          e.dataTransfer.dropEffect = 'copy'
        }}
        onDrop={(e) => {
          const interpolation = readInterpolationDragData(e)
          if (!interpolation) return

          e.preventDefault()
          const target = e.target instanceof HTMLTextAreaElement ? e.target : null
          const selectionStart = target?.selectionStart ?? editorValue.length
          const selectionEnd = target?.selectionEnd ?? editorValue.length
          const nextValue = insertInterpolationAtSelection(
            editorValue,
            interpolation,
            selectionStart,
            selectionEnd,
          )
          onChange(parseStructuredValue(nextValue))
        }}
        style={{ fontFamily: '"Fira code", "Fira Mono", monospace', fontSize: 13 }}
      />
    </div>
  )
}

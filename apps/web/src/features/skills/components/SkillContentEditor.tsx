import React from 'react'
import EditorImport from 'react-simple-code-editor'
import Prism from 'prismjs'
import 'prismjs/components/prism-markdown'
import { cn } from '@/lib/cn'

interface EditorProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
  onValueChange: (value: string) => void
  highlight: (value: string) => string | React.ReactNode
  padding?: number | { top?: number; right?: number; bottom?: number; left?: number }
  textareaClassName?: string
  preClassName?: string
  placeholder?: string
}

// Defensive CJS interop — depending on Vite's pre-bundle state the default
// import may resolve to the component itself OR to a `{ default: Component }`
// wrapper. Drill at most two levels to land on something React can render.
// (Same pattern already used in JsonCodeView — keep them in sync.)
const Editor = (() => {
  let candidate: unknown = EditorImport
  for (let i = 0; i < 2; i++) {
    if (typeof candidate === 'function') break
    if (
      candidate &&
      typeof candidate === 'object' &&
      'default' in (candidate as Record<string, unknown>) &&
      (candidate as Record<string, unknown>).default
    ) {
      candidate = (candidate as { default: unknown }).default
      continue
    }
    break
  }
  return candidate as React.ComponentType<EditorProps>
})()

interface SkillContentEditorProps {
  value: string
  onChange: (next: string) => void
  placeholder?: string
  className?: string
}

/**
 * Markdown body editor for a skill.
 *
 * react-simple-code-editor wraps a contenteditable-style textarea with
 * Prism syntax highlighting. ~30KB total (vs ~3MB for Monaco) and the
 * same package CodeRenderer / JsonCodeView already use. The Prism
 * markdown grammar covers headings, lists, fenced code, links,
 * bold/italic, blockquotes — everything a skill body actually needs.
 */
export function SkillContentEditor({ value, onChange, placeholder, className }: SkillContentEditorProps) {
  return (
    <div
      className={cn(
        'flex-1 overflow-auto rounded-[8px] border border-border-faint bg-bg',
        'focus-within:border-border focus-within:bg-surface',
        'transition-[background-color,border-color] [transition-duration:120ms]',
        className,
      )}
    >
      <Editor
        value={value}
        onValueChange={onChange}
        highlight={code => Prism.highlight(code, Prism.languages.markdown, 'markdown')}
        padding={16}
        placeholder={placeholder}
        textareaClassName="outline-none"
        preClassName="font-mono"
        style={{
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          fontSize: 13,
          lineHeight: 1.6,
          minHeight: '100%',
        }}
      />
    </div>
  )
}

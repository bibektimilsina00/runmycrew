import type { RendererProps } from '../types'
import { ExpressionEditor } from '../expression/ExpressionEditor'

/**
 * Single text field for string properties. Mixed plain-text + embedded
 * `{{ expression }}` blocks live in one editor — completions, syntax
 * highlighting, and ghost preview all activate when the caret enters a
 * `{{ … }}` region, and stand down for free text.
 *
 * Legacy `=expression` saves are transparently migrated to
 * `{{ expression }}` by `ExpressionEditor` on first edit. The backend
 * resolver keeps a silent fallback for any old graph that hasn't been
 * touched since the migration.
 */
export function StringRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const str = value === undefined || value === null ? '' : String(value)
  const opts = prop.typeOptions ?? {}
  const multiline = Boolean(opts.multiline)
  const rows = typeof opts.rows === 'number' ? opts.rows : 3

  return (
    <ExpressionEditor
      value={str}
      onChange={onChange}
      placeholder={prop.placeholder}
      multiline={multiline}
      rows={rows}
      disabled={disabled}
    />
  )
}

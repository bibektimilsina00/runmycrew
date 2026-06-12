import { Textarea } from '@/shared/components'
import type { RendererProps } from '../types'

const LANGUAGE_LABELS: Record<string, string> = {
  python: 'Python',
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  json: 'JSON',
  sql: 'SQL',
  bash: 'Bash',
}

export function CodeRenderer({ prop, value, onChange, disabled }: RendererProps) {
  const str = value === undefined || value === null ? '' : String(value)
  const opts = prop.typeOptions ?? {}
  const language = typeof opts.language === 'string' ? opts.language : undefined
  const rows = typeof opts.rows === 'number' ? opts.rows : 8

  return (
    <div className="flex flex-col gap-1">
      {language && (
        <div className="flex items-center gap-1.5">
          <span className="rounded-[4px] border border-border-faint bg-surface px-1.5 py-0.5 font-mono text-[10px] text-text-faint">
            {LANGUAGE_LABELS[language] ?? language}
          </span>
        </div>
      )}
      <Textarea
        value={str}
        onChange={e => onChange(e.target.value)}
        rows={rows}
        spellCheck={false}
        placeholder={prop.placeholder ?? `# Write ${language ?? 'code'} here`}
        disabled={disabled}
        className="rounded-[5px] font-mono text-[11px] leading-relaxed"
      />
    </div>
  )
}

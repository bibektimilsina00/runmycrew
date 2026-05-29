import { Textarea } from '@/shared/components'

interface ExpressionInputProps {
  value: unknown
  onChange: (value: unknown) => void
  placeholder?: string
}

export function ExpressionInput({ value, onChange, placeholder }: ExpressionInputProps) {
  return (
    <Textarea
      value={value === undefined || value === null ? '' : String(value)}
      onChange={e => onChange(e.target.value)}
      rows={2}
      spellCheck={false}
      placeholder={placeholder ?? '{{node.output.field}}'}
      className="min-h-[56px] font-mono text-[11px] text-[var(--accent)] leading-relaxed"
    />
  )
}

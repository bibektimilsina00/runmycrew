import { type ReactNode, useId } from 'react'
import { AlertCircle, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/cn'

interface FormFieldProps {
  label?: string
  hint?: string
  error?: string
  success?: string
  required?: boolean
  children: ReactNode
  className?: string
}

export function FormField({ label, hint, error, success, required, children, className }: FormFieldProps) {
  const id = useId()

  return (
    <div className={cn('flex flex-col gap-1.5', className)} data-state={error ? 'error' : success ? 'success' : 'idle'}>
      {label && (
        <label
          htmlFor={id}
          className="text-xs font-medium text-text-mute select-none"
        >
          {label}
          {required && <span className="text-err ml-1" aria-hidden="true">*</span>}
          {required && <span className="sr-only">(required)</span>}
        </label>
      )}

      {/* Inject the id into the first child input */}
      <div className="[&_input]:first:[&_div]:id-inject [&_textarea]:first:[&_div]:id-inject">
        {children}
      </div>

      {/* Error message */}
      {error && (
        <p role="alert" className="flex items-center gap-1 text-xs text-err">
          <AlertCircle size={11} className="shrink-0" />
          {error}
        </p>
      )}

      {/* Success message */}
      {success && !error && (
        <p className="flex items-center gap-1 text-xs text-ok">
          <CheckCircle size={11} className="shrink-0" />
          {success}
        </p>
      )}

      {/* Hint — shown when no error/success */}
      {hint && !error && !success && (
        <p className="text-xs font-normal text-text-faint leading-relaxed">{hint}</p>
      )}
    </div>
  )
}

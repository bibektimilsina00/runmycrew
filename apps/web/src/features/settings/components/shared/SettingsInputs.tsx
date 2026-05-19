import React from 'react'
import { Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button, type ButtonProps } from '@/components/ui'

interface SettingsSearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  containerClassName?: string
}

export const SettingsSearchInput: React.FC<SettingsSearchInputProps> = ({
  containerClassName,
  className,
  ...props
}) => (
  <div className={cn('relative min-w-0 flex-1 group', containerClassName)}>
    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-muted)] group-focus-within:text-white transition-colors" />
    <input
      type="text"
      className={cn(
        'w-full h-[32px] pl-9 pr-4 rounded-lg bg-[var(--surface-2)] border border-[var(--border-default)]',
        'text-[13px] text-white placeholder-[var(--text-muted)]',
        'focus:outline-none focus:border-[var(--brand-accent)] focus:ring-1 focus:ring-[var(--brand-accent)] transition-all',
        className,
      )}
      {...props}
    />
  </div>
)

interface SettingsButtonProps extends Omit<ButtonProps, 'size'> {
  size?: 'sm' | 'md'
}

/** Thin wrapper around Button with settings-appropriate defaults. */
export const SettingsButton: React.FC<SettingsButtonProps> = ({
  variant = 'secondary',
  size = 'md',
  className,
  ...props
}) => (
  <Button
    variant={variant}
    size={size === 'sm' ? 'sm' : 'md'}
    className={cn('shrink-0 whitespace-nowrap', className)}
    {...props}
  />
)

import React from 'react'
import { cn } from '@/lib/utils'
import { Spinner } from './spinner'

const variantClasses = {
  primary:   'bg-white text-black font-semibold hover:bg-zinc-200 shadow-sm',
  secondary: 'bg-[var(--surface-3)] border border-[var(--border-default)] text-[var(--text-primary)] font-medium hover:bg-[var(--surface-hover)]',
  accent:    'bg-[var(--brand-accent)] text-white font-semibold hover:bg-[var(--brand-accent-hover)] shadow-lg',
  ghost:     'bg-transparent text-[var(--text-muted)] hover:text-white hover:bg-[var(--surface-hover)]',
  danger:    'bg-red-500 text-white font-semibold hover:bg-red-600',
}

const sizeClasses = {
  xs: 'h-[24px] px-2 text-[11px] rounded-md gap-1',
  sm: 'h-[28px] px-2.5 text-[12px] rounded-md gap-1.5',
  md: 'h-[32px] px-3 text-[13px] rounded-lg gap-2',
  lg: 'py-2.5 px-4 text-[14px] rounded-lg gap-2',
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variantClasses
  size?: keyof typeof sizeClasses
  isLoading?: boolean
  fullWidth?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  disabled,
  className,
  children,
  ...props
}, ref) => (
  <button
    ref={ref}
    disabled={disabled || isLoading}
    className={cn(
      'inline-flex items-center justify-center transition-all duration-150',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-accent)]/50',
      '[&_svg]:shrink-0 [&_svg]:size-[1em]',
      variantClasses[variant],
      sizeClasses[size],
      fullWidth && 'w-full',
      className,
    )}
    {...props}
  >
    {isLoading ? (
      <Spinner size={size === 'lg' ? 'sm' : 'xs'} color="current" />
    ) : leftIcon}
    {children && <span>{children}</span>}
    {!isLoading && rightIcon}
  </button>
))

Button.displayName = 'Button'

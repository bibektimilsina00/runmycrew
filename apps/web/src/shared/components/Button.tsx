import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { cn } from '@/lib/cn'
import { Spinner } from './Spinner'

/**
 * Variants:
 * primary     — accent indigo CTA (the brand primary across the app)
 * secondary   — surface + border, default action
 * outline     — transparent + border, secondary action
 * ghost       — no border, hover only, nav/tertiary
 * destructive — filled red, destructive actions
 * danger      — alias for destructive (backward compat)
 * subtle      — alias for secondary (backward compat)
 * icon        — square icon-only, 36×36, expanded touch area
 * icon-sm     — square icon-only, 28×28, expanded touch area
 */

type Variant = 'secondary' | 'subtle' | 'primary' | 'danger' | 'destructive' | 'outline' | 'ghost' | 'icon' | 'icon-sm'
type Size    = 'sm' | 'md'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  loading?: boolean
}

const base = [
  'inline-flex items-center justify-center shrink-0 select-none',
  'font-medium transition-[background,border-color,color,opacity,transform] [transition-duration:120ms]',
  'active:scale-[0.97] active:[transition-duration:60ms]',
  'disabled:opacity-40 disabled:pointer-events-none disabled:active:scale-100',
  '[&_svg]:shrink-0',
].join(' ')

const secondaryCls = [
  'bg-surface border border-border-faint text-text',
  '[box-shadow:var(--btn-shadow)]',
  'hover:bg-surface-2 hover:border-border-soft',
  '[&_svg]:text-text-mute',
].join(' ')

const destructiveCls = [
  'bg-[var(--danger-bg)] border border-[var(--danger-border)] text-white',
  'hover:bg-[var(--danger-bg-hover)]',
  '[&_svg]:text-white',
].join(' ')

const variants: Record<Variant, string> = {
  primary:     'bg-[var(--accent)] border border-[var(--accent)] text-white hover:brightness-110 [&_svg]:text-white',
  secondary:   secondaryCls,
  subtle:      secondaryCls,
  danger:      destructiveCls,
  destructive: destructiveCls,
  outline:     'bg-transparent border border-border-faint text-text hover:bg-surface hover:border-border-soft [&_svg]:text-text-mute',
  ghost:       'bg-transparent border border-transparent text-text-mute hover:bg-surface hover:text-text [&_svg]:text-text-mute hover:[&_svg]:text-text',
  icon: [
    'relative bg-transparent border border-border-faint text-text-mute',
    'hover:bg-surface hover:text-text',
    'w-9 h-9 rounded-[8px]',
    'before:absolute before:inset-[-4px] before:content-[""]',
    '[&_svg]:w-[15px] [&_svg]:h-[15px]',
  ].join(' '),
  'icon-sm': [
    'relative bg-transparent border border-border-faint text-text-mute',
    'hover:bg-surface hover:text-text',
    'w-7 h-7 rounded-[6px]',
    'before:absolute before:inset-[-7px] before:content-[""]',
    '[&_svg]:w-[13px] [&_svg]:h-[13px]',
  ].join(' '),
}

const sizes: Record<Size, string> = {
  sm: 'h-7 px-3 text-xs gap-1.5 rounded-[6px] [&_svg]:w-3 [&_svg]:h-3',
  md: 'h-9 px-4 text-sm gap-2 rounded-[8px] [&_svg]:w-3.5 [&_svg]:h-3.5',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'secondary', size = 'md', leftIcon, rightIcon, loading, disabled, children, ...props }, ref) => {
    const isIcon = variant === 'icon' || variant === 'icon-sm'

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading}
        className={cn(base, variants[variant], !isIcon && sizes[size], className)}
        {...props}
      >
        {loading
          ? <Spinner size={isIcon || size === 'sm' ? 'xs' : 'sm'} className="shrink-0" />
          : leftIcon
        }
        {isIcon ? (!loading && children) : children}
        {!loading && rightIcon}
      </button>
    )
  },
)

Button.displayName = 'Button'

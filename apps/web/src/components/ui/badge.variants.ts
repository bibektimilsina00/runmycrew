import { cva, type VariantProps } from 'class-variance-authority'

export const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-[4px] px-2 py-0.5 text-xs font-medium transition-colors border',
  {
    variants: {
      variant: {
        default:     'bg-accent-soft border-accent-line text-accent',
        secondary:   'bg-surface border-border-faint text-text-mute',
        ok:          'bg-[var(--badge-ok-bg)] border-transparent text-ok',
        warn:        'bg-[var(--badge-warn-bg)] border-transparent text-warn',
        err:         'bg-[var(--badge-err-bg)] border-transparent text-err',
        destructive: 'bg-[var(--badge-err-bg)] border-transparent text-err',
        outline:     'bg-transparent border-border-faint text-text',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export type BadgeVariantProps = VariantProps<typeof badgeVariants>

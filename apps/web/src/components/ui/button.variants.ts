import { cva, type VariantProps } from 'class-variance-authority'

export const buttonVariants = cva(
  [
    'inline-flex items-center justify-center shrink-0 select-none whitespace-nowrap',
    'font-medium transition-[background,border-color,color,opacity,transform] duration-[120ms]',
    'active:scale-[0.97] active:duration-[60ms]',
    'disabled:opacity-40 disabled:pointer-events-none disabled:active:scale-100',
    '[&_svg]:shrink-0',
  ].join(' '),
  {
    variants: {
      variant: {
        default:
          'bg-primary border border-primary text-primary-foreground hover:brightness-110 [&_svg]:text-white',
        secondary:
          'bg-surface border border-border-faint text-text [box-shadow:var(--btn-shadow)] hover:bg-surface-2 hover:border-border-soft [&_svg]:text-text-mute',
        outline:
          'bg-transparent border border-border-faint text-text hover:bg-surface hover:border-border-soft [&_svg]:text-text-mute',
        ghost:
          'bg-transparent border border-transparent text-text-mute hover:bg-surface hover:text-text [&_svg]:text-text-mute hover:[&_svg]:text-text',
        destructive:
          'bg-[var(--danger-bg)] border border-[var(--danger-border)] text-white hover:bg-[var(--danger-bg-hover)] [&_svg]:text-white',
        link: 'text-primary underline-offset-4 hover:underline',
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
      },
      size: {
        default: 'h-9 px-4 text-sm gap-2 rounded-[8px] [&_svg]:w-3.5 [&_svg]:h-3.5',
        sm:      'h-7 px-3 text-xs gap-1.5 rounded-[6px] [&_svg]:w-3 [&_svg]:h-3',
        lg:      'h-11 px-6 text-base gap-2 rounded-[10px] [&_svg]:w-4 [&_svg]:h-4',
        icon:    'h-9 w-9 rounded-[8px]',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export type ButtonVariantProps = VariantProps<typeof buttonVariants>

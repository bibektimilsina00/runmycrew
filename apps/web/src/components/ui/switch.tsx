import { forwardRef } from 'react'
import * as SwitchPrimitive from '@radix-ui/react-switch'
import { cn } from '@/lib/cn'

/**
 * RunMyCrew Switch — Radix-backed toggle with RunMyCrew accent.
 */
const Switch = forwardRef<
  React.ElementRef<typeof SwitchPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SwitchPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SwitchPrimitive.Root
    ref={ref}
    className={cn(
      'peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full',
      'border-2 border-transparent',
      'transition-colors [transition-duration:150ms]',
      'bg-surface-2 hover:bg-surface-3',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-bg',
      'disabled:cursor-not-allowed disabled:opacity-40',
      'data-[state=checked]:bg-accent',
      className,
    )}
    {...props}
  >
    <SwitchPrimitive.Thumb
      className={cn(
        'pointer-events-none block h-4 w-4 rounded-full bg-white shadow-sm',
        'ring-0 transition-transform [transition-duration:150ms]',
        'data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0',
      )}
    />
  </SwitchPrimitive.Root>
))

Switch.displayName = SwitchPrimitive.Root.displayName

export { Switch }

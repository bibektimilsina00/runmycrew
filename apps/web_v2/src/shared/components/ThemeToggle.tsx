import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/stores/theme'
import { cn } from '@/lib/cn'

interface ThemeToggleProps {
  className?: string
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { isDark, toggle } = useTheme()

  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className={cn(
        'inline-flex items-center justify-center',
        'w-8 h-8 rounded-[8px]',
        'bg-bg2 border border-border-faint',
        'text-text-mute hover:text-text hover:bg-surface',
        'transition-[background,border-color,color] duration-[120ms]',
        className,
      )}
    >
      {isDark
        ? <Sun size={14} strokeWidth={1.8} />
        : <Moon size={14} strokeWidth={1.8} />
      }
    </button>
  )
}

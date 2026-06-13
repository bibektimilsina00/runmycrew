import { createElement } from 'react'
import * as LucideIcons from 'lucide-react'

interface SkillIconBadgeProps {
  iconName: string
  color: string
  size?: 'sm' | 'md' | 'lg'
}

/** Resolves a Lucide icon by its export name; falls back to BookOpen
 *  when the saved icon name no longer exists in the library. */
function resolveIcon(name: string): LucideIcons.LucideIcon {
  const icons = LucideIcons as unknown as Record<string, LucideIcons.LucideIcon>
  return icons[name] ?? LucideIcons.BookOpen
}

const SIZE_MAP: Record<NonNullable<SkillIconBadgeProps['size']>, { box: string; icon: number }> = {
  sm: { box: 'h-7 w-7', icon: 14 },
  md: { box: 'h-9 w-9', icon: 16 },
  lg: { box: 'h-12 w-12', icon: 22 },
}

export function SkillIconBadge({ iconName, color, size = 'md' }: SkillIconBadgeProps) {
  // Lucide icons indirected through their export name; using `React.createElement`
  // avoids the `react-hooks/static-components` complaint about a JSX component
  // tag whose identifier is defined during render.
  const Icon = resolveIcon(iconName)
  const dims = SIZE_MAP[size]
  return (
    <div
      className={`flex ${dims.box} shrink-0 items-center justify-center rounded-[8px]`}
      style={{ background: `${color}22`, color }}
    >
      {createElement(Icon, { size: dims.icon })}
    </div>
  )
}

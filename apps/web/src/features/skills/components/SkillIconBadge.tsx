import { createElement } from 'react'
import * as LucideIcons from 'lucide-react'

interface SkillIconBadgeProps {
  iconName: string
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

export function SkillIconBadge({ iconName, size = 'md' }: SkillIconBadgeProps) {
  // Solid surface background — the previous color-tinted alpha background
  // looked translucent against the page; users couldn't tell the badge from
  // its surroundings. Neutral surface keeps icons readable on every row.
  const Icon = resolveIcon(iconName)
  const dims = SIZE_MAP[size]
  return (
    <div
      className={`flex ${dims.box} shrink-0 items-center justify-center rounded-[8px] bg-surface text-text-mute`}
    >
      {createElement(Icon, { size: dims.icon })}
    </div>
  )
}

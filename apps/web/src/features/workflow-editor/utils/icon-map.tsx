import React from 'react'
import * as LucideIcons from 'lucide-react'

export const getIcon = (iconName: string): React.ReactNode => {
  const IconComponent = (LucideIcons as unknown as Record<string, React.ElementType>)[iconName] ?? LucideIcons.Globe
  return <IconComponent />
}

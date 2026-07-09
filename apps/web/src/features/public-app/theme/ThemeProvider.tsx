import { useEffect } from 'react'
import type { PublicAppConfig } from '../types/publicAppTypes'

interface ThemeProviderProps {
  config: PublicAppConfig
  children: React.ReactNode
}

/**
 * Applies the owner-authored theme to CSS custom properties + document
 * class so both the public page's own styles and any downstream markdown
 * / renderer inherit the same palette.
 */
export function ThemeProvider({ config, children }: ThemeProviderProps) {
  useEffect(() => {
    const root = document.documentElement
    if (config.primary_color) {
      root.style.setProperty('--app-accent', config.primary_color)
    }
    const mode = config.dark_mode ?? 'auto'
    if (mode === 'dark') root.classList.add('dark')
    if (mode === 'light') root.classList.remove('dark')
    if (mode === 'auto') {
      const mql = window.matchMedia('(prefers-color-scheme: dark)')
      const set = () => root.classList.toggle('dark', mql.matches)
      set()
      mql.addEventListener('change', set)
      return () => mql.removeEventListener('change', set)
    }
    return undefined
  }, [config.primary_color, config.dark_mode])

  return <>{children}</>
}

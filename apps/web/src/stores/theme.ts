import { useState, useEffect, useCallback } from 'react'

export type AppTheme = 'midnight-dark' | 'slate-blue' | 'cyber-orange' | 'light-mint' | 'light-slate'

function getStoredTheme(): AppTheme {
  try {
    const v = localStorage.getItem('fuse-app-theme')
    if (v === 'midnight-dark' || v === 'slate-blue' || v === 'cyber-orange' || v === 'light-mint' || v === 'light-slate') return v
  } catch {
    // Ignore errors
  }
  return 'midnight-dark'
}

function applyTheme(theme: AppTheme) {
  const root = document.documentElement
  
  // Clear all theme classes
  root.classList.remove(
    'theme-midnight-dark',
    'theme-slate-blue',
    'theme-cyber-orange',
    'theme-light-mint',
    'theme-light-slate',
    'light'
  )
  
  // Add the new theme class
  root.classList.add(`theme-${theme}`)
  
  // If it's a light theme, add the 'light' helper class for Tailwind/legacy compatibility
  if (theme.startsWith('light-')) {
    root.classList.add('light')
  }
}

// Apply theme immediately on script load
applyTheme(getStoredTheme())

export function useTheme() {
  const [theme, setThemeState] = useState<AppTheme>(getStoredTheme)

  useEffect(() => {
    applyTheme(theme)
    try {
      localStorage.setItem('fuse-app-theme', theme)
    } catch {
      // ignore
    }
  }, [theme])

  const setTheme = useCallback((t: AppTheme) => setThemeState(t), [])

  const toggle = useCallback(() => {
    setThemeState(current => {
      const themes: AppTheme[] = ['midnight-dark', 'slate-blue', 'cyber-orange', 'light-mint', 'light-slate']
      const currentIndex = themes.indexOf(current)
      const nextIndex = (currentIndex + 1) % themes.length
      return themes[nextIndex]
    })
  }, [])

  return {
    theme,
    setTheme,
    toggle,
    isDark: !theme.startsWith('light-'),
  }
}

import { useState, useEffect, useCallback } from 'react'

type Theme = 'dark' | 'light'

function getStored(): Theme {
  try {
    const v = localStorage.getItem('fuse-theme')
    if (v === 'light' || v === 'dark') return v
  } catch {
    // Ignore localStorage access errors (e.g. cookies disabled or sandboxed iframe)
  }
  return 'dark'
}

function applyTheme(theme: Theme) {
  const root = document.documentElement
  if (theme === 'light') {
    root.classList.add('light')
  } else {
    root.classList.remove('light')
  }
}

// Apply immediately on module load (avoids flash)
applyTheme(getStored())

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(getStored)

  useEffect(() => {
    applyTheme(theme)
    try {
      localStorage.setItem('fuse-theme', theme)
    } catch {
      // Ignore localStorage write errors
    }
  }, [theme])

  const setTheme = useCallback((t: Theme) => setThemeState(t), [])
  const toggle   = useCallback(() => setThemeState(t => t === 'dark' ? 'light' : 'dark'), [])

  return { theme, setTheme, toggle, isDark: theme === 'dark' }
}

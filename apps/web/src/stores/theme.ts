import { useState, useEffect, useCallback } from 'react'

type Theme = 'dark' | 'light'

/**
 * Color schemes layered on top of the base dark theme.
 * `linear` is the default and uses :root tokens directly — no `data-theme`
 * attribute is set. The other five swap surface + accent tokens via
 * `:root[data-theme='<name>']` blocks defined in `index.css`.
 */
export type ColorScheme = 'linear' | 'slate' | 'indigo' | 'emerald' | 'ember' | 'plum'

const SCHEMES: readonly ColorScheme[] = ['linear', 'slate', 'indigo', 'emerald', 'ember', 'plum']

function getStored(): Theme {
  try {
    const v = localStorage.getItem('fuse-theme')
    if (v === 'light' || v === 'dark') return v
  } catch {
    // Ignore localStorage access errors
  }
  return 'dark'
}

function getStoredScheme(): ColorScheme {
  try {
    const v = localStorage.getItem('fuse-scheme')
    if (v && (SCHEMES as readonly string[]).includes(v)) return v as ColorScheme
  } catch {
    // Ignore
  }
  // Slate is the default scheme — slightly lifted backgrounds vs the
  // near-black Linear preset; reads cleaner on most monitors.
  return 'slate'
}

function applyTheme(theme: Theme) {
  const root = document.documentElement
  if (theme === 'light') root.classList.add('light')
  else root.classList.remove('light')
}

function applyScheme(scheme: ColorScheme) {
  const root = document.documentElement
  if (scheme === 'linear') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', scheme)
}

// Apply immediately on module load (avoids flash)
applyTheme(getStored())
applyScheme(getStoredScheme())

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(getStored)

  useEffect(() => {
    applyTheme(theme)
    try { localStorage.setItem('fuse-theme', theme) } catch { /* ignore */ }
  }, [theme])

  const setTheme = useCallback((t: Theme) => setThemeState(t), [])
  const toggle   = useCallback(() => setThemeState(t => t === 'dark' ? 'light' : 'dark'), [])

  return { theme, setTheme, toggle, isDark: theme === 'dark' }
}

export function useColorScheme() {
  const [scheme, setSchemeState] = useState<ColorScheme>(getStoredScheme)

  useEffect(() => {
    applyScheme(scheme)
    try { localStorage.setItem('fuse-scheme', scheme) } catch { /* ignore */ }
  }, [scheme])

  const setScheme = useCallback((s: ColorScheme) => setSchemeState(s), [])

  return { scheme, setScheme, schemes: SCHEMES }
}

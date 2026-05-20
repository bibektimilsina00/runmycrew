import { useState, useCallback } from 'react'
import type { CopilotSettings } from './use-copilot'

const STORAGE_KEY = 'fuse-copilot-settings'

const DEFAULT_SETTINGS: CopilotSettings & { modelMode: 'manual' | 'dynamic' } = {
  provider: 'anthropic',
  model: '',
  credentialId: null,
  modelMode: 'dynamic',
}

export function useCopilotSettings(_workflowId: string) {
  const [settings, setSettings] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? { ...DEFAULT_SETTINGS, ...JSON.parse(stored) } : DEFAULT_SETTINGS
    } catch {
      return DEFAULT_SETTINGS
    }
  })

  const updateSettings = useCallback((next: Partial<typeof DEFAULT_SETTINGS>) => {
    setSettings((prev) => {
      const merged = { ...prev, ...next }
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(merged))
      } catch {
        // ignore storage errors
      }
      return merged
    })
  }, [])

  return { settings, updateSettings, isLoaded: true }
}

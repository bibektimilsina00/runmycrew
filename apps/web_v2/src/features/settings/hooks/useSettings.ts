import { useState, useEffect } from 'react'
import { settingsAPI } from '../services/settingsAPI'
import type { ApiKey } from '../types/settingsTypes'

export function useSettings() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [isGenerating, setIsGenerating] = useState(false)

  useEffect(() => {
    settingsAPI.getApiKeys().then(setApiKeys)
  }, [])

  const createApiKey = async (name: string) => {
    setIsGenerating(true)
    try {
      const newKey = await settingsAPI.createApiKey(name)
      setApiKeys(prev => [...prev, newKey])
      return newKey
    } finally {
      setIsGenerating(false)
    }
  }

  const revokeApiKey = async (id: string) => {
    await settingsAPI.revokeApiKey(id)
    setApiKeys(prev => prev.filter(k => k.id !== id))
  }

  return { apiKeys, isGenerating, createApiKey, revokeApiKey }
}

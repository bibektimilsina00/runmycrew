import type { ApiKey } from '../types/settingsTypes'

const MOCK_API_KEYS: ApiKey[] = [
  { id: 'key-1', name: 'Production Daemon Client', token: 'fuse_live_abc123xyz789...', createdAt: 'May 10, 2026' },
  { id: 'key-2', name: 'Staging CLI Client', token: 'fuse_test_def456uvw012...', createdAt: 'May 18, 2026' },
]

export const settingsAPI = {
  getApiKeys: async (): Promise<ApiKey[]> => {
    return MOCK_API_KEYS
  },

  createApiKey: async (name: string): Promise<ApiKey> => {
    return {
      id: `key-${Date.now()}`,
      name,
      token: `fuse_live_${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 10)}...`,
      createdAt: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    }
  },

  revokeApiKey: async (id: string): Promise<void> => {
    // no-op mock
    void id
  },
}

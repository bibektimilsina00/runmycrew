export const settingsKeys = {
  all: ['settings'] as const,
  apiKeys: () => [...settingsKeys.all, 'api-keys'] as const,
}

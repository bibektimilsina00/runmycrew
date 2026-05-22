import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsAPI } from '../services/settingsAPI'
import { settingsKeys } from './keys'
import { authKeys } from '@/features/auth/hooks/keys'
import { useAuthStore } from '@/features/auth/store/authStore'
import type { ApiKey } from '../types/settingsTypes'

export function useSettings() {
  const queryClient = useQueryClient()

  // Fetch developer API keys
  const { data: apiKeys = [], isLoading } = useQuery({
    queryKey: settingsKeys.apiKeys(),
    queryFn: ({ signal }) => settingsAPI.getApiKeys(signal),
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  // Create API key mutation
  const createMutation = useMutation({
    mutationFn: (name: string) => settingsAPI.createApiKey(name),
    onSuccess: () => {
      // Optimitic update is tricky because it returns 'token', so we just invalidate
      queryClient.invalidateQueries({ queryKey: settingsKeys.apiKeys() })
    },
  })

  // Revoke API key mutation
  const revokeMutation = useMutation({
    mutationFn: (id: string) => settingsAPI.revokeApiKey(id),
    onSuccess: (_, id) => {
      queryClient.setQueryData(settingsKeys.apiKeys(), (oldData: ApiKey[] | undefined) => {
        return oldData?.filter(k => k.id !== id)
      })
      queryClient.invalidateQueries({ queryKey: settingsKeys.apiKeys() })
    },
  })

  return {
    apiKeys,
    isLoading,
    isGenerating: createMutation.isPending,
    createApiKey: createMutation.mutateAsync,
    revokeApiKey: revokeMutation.mutateAsync,
  }
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  const setUser = useAuthStore((state) => state.setUser)

  return useMutation({
    mutationFn: ({ fullName, password }: { fullName?: string; password?: string }) =>
      settingsAPI.updateProfile(fullName, password),
    onSuccess: (updatedUser) => {
      // Sync the updated user profile into Zustand store
      setUser(updatedUser)
      // Invalidate the auth 'me' query cache
      queryClient.invalidateQueries({ queryKey: authKeys.me() })
    },
  })
}

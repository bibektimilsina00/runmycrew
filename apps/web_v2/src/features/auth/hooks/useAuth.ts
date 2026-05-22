import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import * as authAPI from '../services/authAPI'
import { authKeys } from './keys'
import type {
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
} from '../types/authType'


/**
 * Custom hook to interact with authentication states and API services.
 * Integrates React Query for server state management and Zustand for global auth state.
 */
export function useAuth() {
  const queryClient = useQueryClient()

  const token = useAuthStore((state) => state.token)
  const user = useAuthStore((state) => state.user)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isLoadingStore = useAuthStore((state) => state.isLoading)
  const errorStore = useAuthStore((state) => state.error)

  const setToken = useAuthStore((state) => state.setToken)
  const setUser = useAuthStore((state) => state.setUser)
  const setLoading = useAuthStore((state) => state.setLoading)
  const setError = useAuthStore((state) => state.setError)
  const clearAuth = useAuthStore((state) => state.logout)

  // React Query for current user profile
  const { data: meData, refetch, isFetching, isLoading: isQueryLoading } = useQuery({
    queryKey: authKeys.me(),
    queryFn: async ({ signal }) => {
      try {
        const profile = await authAPI.getMe(signal)
        setUser(profile)
        return profile
      } catch (err: unknown) {
        // If token is invalid/expired (401), clear authentication state
        const status = err && typeof err === 'object' && 'status' in err ? (err as Record<string, unknown>).status : undefined
        if (status === 401) {
          clearAuth()
        }
        throw err
      }
    },
    enabled: !!token,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnMount: false,
  })

  // Mutation for user login
  const loginMutation = useMutation({
    mutationFn: async ({ payload, signal }: { payload: LoginRequest; signal?: AbortSignal }) => {
      setError(null)
      setLoading(true)
      try {
        const tokenRes = await authAPI.login(payload, signal)
        setToken(tokenRes.access_token)
        
        // Fetch profile immediately and update query cache
        const profile = await queryClient.fetchQuery({
          queryKey: authKeys.me(),
          queryFn: ({ signal: querySignal }) => authAPI.getMe(querySignal),
        })
        setUser(profile)
        return profile
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Login failed'
        setError(message)
        throw err
      } finally {
        setLoading(false)
      }
    },
  })

  // Mutation for user registration
  const registerMutation = useMutation({
    mutationFn: async ({ payload, signal }: { payload: RegisterRequest; signal?: AbortSignal }) => {
      setError(null)
      setLoading(true)
      try {
        await authAPI.register(payload, signal)
        
        // Auto-login upon successful registration
        const tokenRes = await authAPI.login({
          email: payload.email,
          password: payload.password,
        }, signal)
        setToken(tokenRes.access_token)

        const profile = await queryClient.fetchQuery({
          queryKey: authKeys.me(),
          queryFn: ({ signal: querySignal }) => authAPI.getMe(querySignal),
        })
        setUser(profile)
        return profile
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Registration failed'
        setError(message)
        throw err
      } finally {
        setLoading(false)
      }
    },
  })

  // Mutation for forgot password
  const forgotPasswordMutation = useMutation({
    mutationFn: async ({ payload, signal }: { payload: ForgotPasswordRequest; signal?: AbortSignal }) => {
      setError(null)
      setLoading(true)
      try {
        return await authAPI.forgotPassword(payload, signal)
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Forgot password request failed'
        setError(message)
        throw err
      } finally {
        setLoading(false)
      }
    },
  })

  // Mutation for reset password
  const resetPasswordMutation = useMutation({
    mutationFn: async ({ payload, signal }: { payload: ResetPasswordRequest; signal?: AbortSignal }) => {
      setError(null)
      setLoading(true)
      try {
        return await authAPI.resetPassword(payload, signal)
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Reset password request failed'
        setError(message)
        throw err
      } finally {
        setLoading(false)
      }
    },
  })

  /**
   * Logs in a user, retrieves the session token, and fetches their profile.
   */
  const login = useCallback(
    async (payload: LoginRequest) => {
      return loginMutation.mutateAsync({ payload })
    },
    [loginMutation]
  )

  /**
   * Registers a new user account, then automatically logs them in.
   */
  const register = useCallback(
    async (payload: RegisterRequest) => {
      return registerMutation.mutateAsync({ payload })
    },
    [registerMutation]
  )

  /**
   * Triggers the forgot password flow.
   */
  const forgotPassword = useCallback(
    async (payload: ForgotPasswordRequest) => {
      return forgotPasswordMutation.mutateAsync({ payload })
    },
    [forgotPasswordMutation]
  )

  /**
   * Resets the password using reset token and new password.
   */
  const resetPassword = useCallback(
    async (payload: ResetPasswordRequest) => {
      return resetPasswordMutation.mutateAsync({ payload })
    },
    [resetPasswordMutation]
  )

  /**
   * Fetches the current user profile manually.
   */
  const fetchCurrentUser = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await refetch()
      if (result.isError) {
        throw result.error
      }
      return result.data
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch user profile'
      setError(message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [refetch, setError, setLoading])

  /**
   * Logs out the user and clears all credentials.
   */
  const logout = useCallback(() => {
    clearAuth()
    queryClient.clear()
  }, [clearAuth, queryClient])

  // Combine loading states from Zustand, mutations, and profile fetching
  const isLoading =
    isLoadingStore ||
    loginMutation.isPending ||
    registerMutation.isPending ||
    forgotPasswordMutation.isPending ||
    resetPasswordMutation.isPending ||
    isFetching

  // Combine error states from Zustand and mutations
  const error =
    errorStore ||
    (loginMutation.error?.message ?? null) ||
    (registerMutation.error?.message ?? null) ||
    (forgotPasswordMutation.error?.message ?? null) ||
    (resetPasswordMutation.error?.message ?? null)

  // We are restoring the session if we have a token, but the user profile is not loaded yet and the query is running
  const isRestoringSession = !!token && !meData && !user && isQueryLoading

  return {
    token,
    user: meData || user,
    isAuthenticated: isAuthenticated && !!(meData || user),
    isLoading,
    isRestoringSession,
    error,
    login,
    register,
    forgotPassword,
    resetPassword,
    logout,
    fetchCurrentUser,
  }
}

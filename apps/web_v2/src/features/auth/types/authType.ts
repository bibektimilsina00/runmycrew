import { z } from 'zod'

/**
 * Zod schema and TypeScript type for User profile.
 */
export const UserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  full_name: z.string().nullish(),
  avatar_url: z.string().nullish(),
  is_active: z.boolean().optional(),
  created_at: z.string().optional(),
})

export type User = z.infer<typeof UserSchema>

/**
 * Zod schema and TypeScript type for Token Response.
 */
export const TokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
})

export type TokenResponse = z.infer<typeof TokenResponseSchema>

/**
 * Zod schema and TypeScript type for Login Request payload.
 */
export const LoginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string(),
})

export type LoginRequest = z.infer<typeof LoginRequestSchema>

/**
 * Zod schema and TypeScript type for Register Request payload.
 */
export const RegisterRequestSchema = z.object({
  email: z.string().email(),
  password: z.string(),
  full_name: z.string().optional(),
})

export type RegisterRequest = z.infer<typeof RegisterRequestSchema>

/**
 * Zod schema and TypeScript type for Forgot Password Request payload.
 */
export const ForgotPasswordRequestSchema = z.object({
  email: z.string().email(),
})

export type ForgotPasswordRequest = z.infer<typeof ForgotPasswordRequestSchema>

/**
 * Zod schema and TypeScript type for Reset Password Request payload.
 */
export const ResetPasswordRequestSchema = z.object({
  token: z.string(),
  new_password: z.string().min(8, 'Password must be at least 8 characters long'),
})

export type ResetPasswordRequest = z.infer<typeof ResetPasswordRequestSchema>

/**
 * Zod schema and TypeScript type for status message responses.
 */
export const MessageResponseSchema = z.object({
  message: z.string(),
})

export type MessageResponse = z.infer<typeof MessageResponseSchema>

/**
 * The authentication state stored in Zustand and accessed by hooks.
 */
export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}


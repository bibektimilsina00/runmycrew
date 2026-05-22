import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  UserSchema,
  TokenResponseSchema,
  MessageResponseSchema,
  type User,
  type TokenResponse,
  type LoginRequest,
  type RegisterRequest,
  type ForgotPasswordRequest,
  type ResetPasswordRequest,
  type MessageResponse,
} from '../types/authType'

/**
 * Log in a user with email and password, returning an access token.
 * 
 * @param data - The login request payload.
 * @param signal - Optional AbortSignal for request cancellation.
 * @returns The token response containing the JWT token.
 */
export async function login(data: LoginRequest, signal?: AbortSignal): Promise<TokenResponse> {
  return requestJson(TokenResponseSchema, {
    url: API_ROUTES.LOGIN,
    method: 'POST',
    data,
    signal,
  })
}

/**
 * Register a new user, returning the newly created User profile.
 * 
 * @param data - The registration request payload.
 * @param signal - Optional AbortSignal for request cancellation.
 * @returns The created User profile.
 */
export async function register(data: RegisterRequest, signal?: AbortSignal): Promise<User> {
  return requestJson(UserSchema, {
    url: API_ROUTES.REGISTER,
    method: 'POST',
    data,
    signal,
  })
}

/**
 * Retrieve the current user's profile based on the stored token.
 * 
 * @param signal - Optional AbortSignal for request cancellation.
 * @returns The current logged-in User profile.
 */
export async function getMe(signal?: AbortSignal): Promise<User> {
  return requestJson(UserSchema, {
    url: API_ROUTES.ME,
    method: 'GET',
    signal,
  })
}

/**
 * Request a password reset link to be sent to the user's email.
 * 
 * @param data - The forgot password payload (email).
 * @param signal - Optional AbortSignal for request cancellation.
 * @returns The response message.
 */
export async function forgotPassword(
  data: ForgotPasswordRequest,
  signal?: AbortSignal
): Promise<MessageResponse> {
  return requestJson(MessageResponseSchema, {
    url: API_ROUTES.FORGOT_PASSWORD,
    method: 'POST',
    data,
    signal,
  })
}

/**
 * Reset the user's password using a token and the new password.
 * 
 * @param data - The reset password payload (token and new password).
 * @param signal - Optional AbortSignal for request cancellation.
 * @returns The response message.
 */
export async function resetPassword(
  data: ResetPasswordRequest,
  signal?: AbortSignal
): Promise<MessageResponse> {
  return requestJson(MessageResponseSchema, {
    url: API_ROUTES.RESET_PASSWORD,
    method: 'POST',
    data,
    signal,
  })
}



import { z } from 'zod'
import axios from 'axios'
import {
  AppMessageSchema,
  PublicAppSchema,
  SendMessageOutSchema,
  SessionEnvelopeSchema,
  type PublicApp,
  type SendMessageOut,
  type SessionEnvelope,
  type AppMessage,
} from '../types/publicAppTypes'

/**
 * The public app page is unauthenticated. It MUST NOT pick up the
 * currently-logged-in user's Bearer token (which would leak the owner's
 * identity to what should be a public surface) nor the workspace header.
 *
 * We therefore use a fresh axios instance instead of the shared apiClient.
 * Visitor identity is the session cookie set by /session, and
 * `withCredentials` keeps that cookie riding every request.
 */
const publicClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
  timeout: 20000,
})

async function req<S extends z.ZodTypeAny>(
  schema: S,
  cfg: Parameters<typeof publicClient.request>[0],
): Promise<z.output<S>> {
  const resp = await publicClient.request(cfg)
  const parsed = schema.safeParse(resp.data)
  if (!parsed.success) {
    throw new Error(`Response shape mismatch: ${parsed.error.message}`)
  }
  return parsed.data
}

export const publicAppAPI = {
  base: (ws: string, slug: string) => `/apps/${ws}/${slug}`,

  getConfig: (ws: string, slug: string, signal?: AbortSignal): Promise<PublicApp> =>
    req(PublicAppSchema, { url: publicAppAPI.base(ws, slug), method: 'GET', signal }),

  ensureSession: (ws: string, slug: string): Promise<SessionEnvelope> =>
    req(SessionEnvelopeSchema, {
      url: `${publicAppAPI.base(ws, slug)}/session`,
      method: 'POST',
    }),

  history: (ws: string, slug: string): Promise<AppMessage[]> =>
    req(z.array(AppMessageSchema), {
      url: `${publicAppAPI.base(ws, slug)}/history`,
      method: 'GET',
    }),

  sendMessage: (
    ws: string,
    slug: string,
    body: { message: string; form_data?: Record<string, unknown> },
  ): Promise<SendMessageOut> =>
    req(SendMessageOutSchema, {
      url: `${publicAppAPI.base(ws, slug)}/message`,
      method: 'POST',
      data: body,
    }),

  /**
   * Stream URL a component feeds to `new EventSource(url, { withCredentials: true })`
   * to receive assistant token deltas + artifact frames. The path is
   * absolute (server-provided) so callers don't have to build it.
   */
  streamUrl: (streamPath: string) => {
    const base = import.meta.env.VITE_API_URL || '/api/v1'
    // Server hands us `/api/v1/apps/.../stream/<id>` which is already
    // absolute at the origin, so just return it.
    if (streamPath.startsWith('/')) return streamPath
    return `${base}/${streamPath.replace(/^\/+/, '')}`
  },
}

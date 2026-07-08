import { z } from 'zod'

export const ProviderFieldSchema = z.object({
  id: z.string(),
  label: z.string(),
  type: z.string(),
  placeholder: z.string(),
})
export type ProviderField = z.infer<typeof ProviderFieldSchema>

export const ProviderSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.enum(['oauth', 'api_key']),
  description: z.string(),
  // Backend owns the brand identity: `icon_slug` resolves against
  // theSVG; `color` is the tile background CSS hex. Adding a new
  // integration in the backend ships its visual identity along with
  // it — frontend doesn't need a release.
  icon_slug: z.string().nullable().optional(),
  color: z.string().nullable().optional(),
  fields: z.array(ProviderFieldSchema).nullable().optional(),
  hint: z.string().nullable().optional(),
  scopes: z.array(z.string()).nullable().optional(),
  // Brand group (google/aws/microsoft/…) — collapses per-service
  // providers under one tile in the picker. `null` = ungrouped.
  brand: z.string().nullable().optional(),
})
export type Provider = z.infer<typeof ProviderSchema>

export const CredentialSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  type: z.string(),
  meta: z.record(z.string(), z.unknown()).nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type Credential = z.infer<typeof CredentialSchema>

export const OAuthUrlSchema = z.object({ url: z.string(), state: z.string() })
export type OAuthUrl = z.infer<typeof OAuthUrlSchema>

export const AuditLogSchema = z.object({
  id: z.string(),
  action: z.string(),
  resource_type: z.string(),
  resource_id: z.string(),
  resource_name: z.string(),
  meta: z.record(z.string(), z.unknown()).nullable().optional(),
  created_at: z.string(),
  user_email: z.string().nullable().optional(),
  user_name: z.string().nullable().optional(),
})
export type AuditLogEntry = z.infer<typeof AuditLogSchema>

export function credentialStatus(cred: Credential): 'ok' | 'warn' | 'err' {
  const expiresAt = (cred.meta as Record<string, unknown> | null)?.expires_at
  if (!expiresAt || typeof expiresAt !== 'string') return 'ok'
  const exp = new Date(expiresAt)
  const now = new Date()
  if (exp <= now) return 'err'
  if (exp.getTime() - now.getTime() < 7 * 24 * 60 * 60 * 1000) return 'warn'
  return 'ok'
}

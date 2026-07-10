import { z } from 'zod'

export const SuggestedPromptSchema = z.object({
  label: z.string(),
  prompt: z.string(),
})

export const InputFieldSchema = z.object({
  name: z.string(),
  label: z.string().optional().default(''),
  type: z.string().default('text'),
  required: z.boolean().optional().default(false),
  placeholder: z.string().optional().default(''),
  help_text: z.string().optional().default(''),
})

export const PublicAppConfigSchema = z.object({
  welcome_headline: z.string().optional().default(''),
  welcome_sub: z.string().optional().default(''),
  welcome_message: z.string().optional().default(''),
  suggested_prompts: z.array(SuggestedPromptSchema).optional().default([]),
  input_fields: z.array(InputFieldSchema).optional().default([]),
  allow_history: z.boolean().optional().default(true),
  output_target: z.string().optional().default('both'),
  system_persona_id: z.string().nullable().optional(),
  primary_color: z.string().optional(),
  logo_url: z.string().optional(),
  dark_mode: z.string().optional(),
  show_powered_by: z.boolean().optional().default(true),
}).passthrough()

export const PublicAppSchema = z.object({
  workflow_id: z.string(),
  workspace_slug: z.string(),
  app_slug: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  mode: z.string(),
  auth_mode: z.string(),
  config: PublicAppConfigSchema,
  public_url: z.string().nullable().optional(),
})
export type PublicApp = z.infer<typeof PublicAppSchema>
export type PublicAppConfig = z.infer<typeof PublicAppConfigSchema>
export type SuggestedPrompt = z.infer<typeof SuggestedPromptSchema>
export type InputField = z.infer<typeof InputFieldSchema>

export const SessionSchema = z.object({
  id: z.string(),
  // Exactly one of the two is set — the session's chat-app source.
  workflow_id: z.string().nullable().optional(),
  crew_id: z.string().nullable().optional(),
  cookie_id: z.string(),
  user_id: z.string().nullable(),
  first_seen_at: z.string(),
  last_seen_at: z.string(),
  message_count: z.number(),
  total_cost_usd: z.number(),
  total_tokens: z.number(),
  is_blocked: z.boolean(),
})
export type Session = z.infer<typeof SessionSchema>

export const AppMessageSchema = z.object({
  id: z.string(),
  session_id: z.string(),
  role: z.string(),
  content: z.string(),
  artifacts: z.array(z.any()),
  execution_id: z.string().nullable(),
  tokens: z.number(),
  cost_usd: z.number(),
  latency_ms: z.number(),
  is_error: z.boolean(),
  created_at: z.string(),
})
export type AppMessage = z.infer<typeof AppMessageSchema>

export const SessionEnvelopeSchema = z.object({
  session: SessionSchema,
  messages: z.array(AppMessageSchema),
})
export type SessionEnvelope = z.infer<typeof SessionEnvelopeSchema>

export const SendMessageOutSchema = z.object({
  message_id: z.string(),
  execution_id: z.string(),
  stream_url: z.string(),
})
export type SendMessageOut = z.infer<typeof SendMessageOutSchema>

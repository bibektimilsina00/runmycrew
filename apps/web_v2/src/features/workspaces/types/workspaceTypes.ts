import { z } from 'zod'

export const WorkspaceRoleSchema = z.enum(['owner', 'admin', 'member', 'viewer'])
export type WorkspaceRole = z.infer<typeof WorkspaceRoleSchema>

export const WorkspaceSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  slug: z.string(),
  owner_id: z.string().uuid(),
  is_personal: z.boolean(),
  avatar_url: z.string().nullable().optional(),
  plan: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
})
export type Workspace = z.infer<typeof WorkspaceSchema>

export const WorkspaceWithRoleSchema = WorkspaceSchema.extend({
  role: WorkspaceRoleSchema,
  member_count: z.number(),
})
export type WorkspaceWithRole = z.infer<typeof WorkspaceWithRoleSchema>

export const WorkspaceUserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  full_name: z.string().nullable().optional(),
  avatar_url: z.string().nullable().optional(),
})
export type WorkspaceUser = z.infer<typeof WorkspaceUserSchema>

export const WorkspaceMemberSchema = z.object({
  id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  user_id: z.string().uuid(),
  role: WorkspaceRoleSchema,
  invited_by: z.string().uuid().nullable().optional(),
  joined_at: z.string(),
  user: WorkspaceUserSchema,
})
export type WorkspaceMember = z.infer<typeof WorkspaceMemberSchema>

export const WorkspaceInviteSchema = z.object({
  id: z.string().uuid(),
  workspace_id: z.string().uuid(),
  email: z.string().email(),
  role: WorkspaceRoleSchema,
  token: z.string(),
  invite_url: z.string(),
  expires_at: z.string(),
  accepted_at: z.string().nullable().optional(),
  created_at: z.string(),
})
export type WorkspaceInvite = z.infer<typeof WorkspaceInviteSchema>

export const InvitePreviewSchema = z.object({
  workspace_id: z.string().uuid(),
  workspace_name: z.string(),
  email: z.string().email(),
  role: WorkspaceRoleSchema,
  expires_at: z.string(),
  accepted_at: z.string().nullable().optional(),
})
export type InvitePreview = z.infer<typeof InvitePreviewSchema>

export interface WorkspaceCreateRequest {
  name: string
}

export interface WorkspaceInviteRequest {
  email: string
  role: WorkspaceRole
  send_email: boolean
}

export interface WorkspaceMemberUpdateRequest {
  role: WorkspaceRole
}

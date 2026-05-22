import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  WorkspaceWithRoleSchema,
  WorkspaceMemberSchema,
  WorkspaceInviteSchema,
  InvitePreviewSchema,
  type WorkspaceCreateRequest,
  type WorkspaceInviteRequest,
  type WorkspaceMemberUpdateRequest,
} from '../types/workspaceTypes'

const WorkspaceListSchema = z.array(WorkspaceWithRoleSchema)
const MemberListSchema = z.array(WorkspaceMemberSchema)

export const workspaceAPI = {
  listWorkspaces: (signal?: AbortSignal) =>
    requestJson(WorkspaceListSchema, { url: API_ROUTES.WORKSPACES, method: 'GET', signal }),

  createWorkspace: (data: WorkspaceCreateRequest) =>
    requestJson(WorkspaceWithRoleSchema, { url: API_ROUTES.WORKSPACES, method: 'POST', data }),

  listMembers: (workspaceId: string, signal?: AbortSignal) =>
    requestJson(MemberListSchema, { url: API_ROUTES.WORKSPACE_MEMBERS(workspaceId), method: 'GET', signal }),

  createInvite: (workspaceId: string, data: WorkspaceInviteRequest) =>
    requestJson(WorkspaceInviteSchema, { url: API_ROUTES.WORKSPACE_INVITES(workspaceId), method: 'POST', data }),

  previewInvite: (token: string, signal?: AbortSignal) =>
    requestJson(InvitePreviewSchema, { url: API_ROUTES.INVITE_PREVIEW(token), method: 'GET', signal }),

  acceptInvite: (token: string) =>
    requestJson(WorkspaceMemberSchema, { url: API_ROUTES.INVITE_ACCEPT(token), method: 'POST' }),

  updateMember: (workspaceId: string, userId: string, data: WorkspaceMemberUpdateRequest) =>
    requestJson(WorkspaceMemberSchema, { url: API_ROUTES.WORKSPACE_MEMBER(workspaceId, userId), method: 'PATCH', data }),

  removeMember: (workspaceId: string, userId: string) =>
    requestJson(z.any(), { url: API_ROUTES.WORKSPACE_MEMBER(workspaceId, userId), method: 'DELETE' }),
}

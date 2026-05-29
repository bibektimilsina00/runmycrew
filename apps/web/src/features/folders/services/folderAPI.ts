import { requestJson } from '@/shared/utils/apiClient'
import { FolderSchema } from '../types/folderTypes'
import { z } from 'zod'

export const folderAPI = {
  list: (signal?: AbortSignal) =>
    requestJson(z.array(FolderSchema), { url: '/folders/', method: 'GET', signal }),
  create: (name: string, parentId?: string | null) =>
    requestJson(FolderSchema, { url: '/folders/', method: 'POST', data: { name, parent_id: parentId } }),
  update: (id: string, name: string) =>
    requestJson(FolderSchema, { url: `/folders/${id}`, method: 'PUT', data: { name } }),
  delete: (id: string) =>
    requestJson(z.any(), { url: `/folders/${id}`, method: 'DELETE' }),
}

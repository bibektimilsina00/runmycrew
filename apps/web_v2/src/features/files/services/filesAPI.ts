import { z } from 'zod'
import apiClient, { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import { FileAssetSchema, FileStatsSchema } from '../types/filesTypes'

const FileAssetListSchema = z.array(FileAssetSchema)

export const filesAPI = {
  list: (signal?: AbortSignal) =>
    requestJson(FileAssetListSchema, { url: API_ROUTES.ASSETS, method: 'GET', signal }),

  stats: (signal?: AbortSignal) =>
    requestJson(FileStatsSchema, { url: API_ROUTES.ASSET_STATS, method: 'GET', signal }),

  upload: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const response = await apiClient.post(API_ROUTES.ASSET_UPLOAD, form, {
      headers: { 'Content-Type': undefined },
    })
    return FileAssetSchema.parse(response.data)
  },

  rename: (id: string, name: string) =>
    requestJson(FileAssetSchema, { url: API_ROUTES.ASSET(id), method: 'PATCH', data: { name } }),

  delete: (id: string) =>
    requestJson(z.unknown(), { url: API_ROUTES.ASSET(id), method: 'DELETE' }),

  downloadBlob: async (id: string) => {
    const response = await apiClient.get<Blob>(API_ROUTES.ASSET_DOWNLOAD(id), {
      responseType: 'blob',
    })
    return response.data
  },

  viewBlob: async (id: string) => {
    const response = await apiClient.get<Blob>(API_ROUTES.ASSET_VIEW(id), {
      responseType: 'blob',
    })
    return response.data
  },
}

import { z } from 'zod'
import apiClient, { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  KnowledgeBaseSchema, KBDetailSchema, SearchResponseSchema,
  KBChunkSchema,
  type KBCreateRequest,
} from '../types/knowledgeTypes'

const ChunkListSchema = z.array(KBChunkSchema)

const KBListSchema = z.array(KnowledgeBaseSchema)
const DocOutSchema = z.object({
  id: z.string(), name: z.string(),
  chunk_count: z.number(), source_type: z.string(),
  status: z.string().default('indexed'),
})

export const knowledgeAPI = {
  list: (signal?: AbortSignal) =>
    requestJson(KBListSchema, { url: API_ROUTES.KB_LIST, method: 'GET', signal }),

  get: (id: string, signal?: AbortSignal) =>
    requestJson(KBDetailSchema, { url: API_ROUTES.KB(id), method: 'GET', signal }),

  create: (data: KBCreateRequest) =>
    requestJson(KnowledgeBaseSchema, { url: API_ROUTES.KB_LIST, method: 'POST', data }),

  update: (id: string, data: Partial<KBCreateRequest>) =>
    requestJson(KnowledgeBaseSchema, { url: API_ROUTES.KB(id), method: 'PATCH', data }),

  delete: (id: string) =>
    requestJson(z.any(), { url: API_ROUTES.KB(id), method: 'DELETE' }),

  addTextDoc: (kbId: string, name: string, text: string) =>
    requestJson(DocOutSchema, {
      url: API_ROUTES.KB_DOC_TEXT(kbId), method: 'POST', data: { name, text },
    }),

  uploadDoc: async (kbId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    // Use apiClient directly — requestJson sets Content-Type: application/json by default
    // which breaks multipart uploads. Let Axios set the correct boundary automatically.
    const res = await apiClient.post(API_ROUTES.KB_DOC_UPLOAD(kbId), form, {
      headers: { 'Content-Type': undefined },  // removes instance default, lets Axios set multipart
    })
    return DocOutSchema.parse(res.data)
  },

  addUrlDoc: (kbId: string, url: string) =>
    requestJson(DocOutSchema, {
      url: API_ROUTES.KB_DOC_URL(kbId), method: 'POST', data: { url },
    }),

  deleteDoc: (kbId: string, docId: string) =>
    requestJson(z.any(), { url: API_ROUTES.KB_DOC(kbId, docId), method: 'DELETE' }),

  search: (kbId: string, query: string, top_k = 5) =>
    requestJson(SearchResponseSchema, {
      url: API_ROUTES.KB_SEARCH(kbId), method: 'POST', data: { query, top_k },
    }),

  listChunks: (kbId: string, docId: string, signal?: AbortSignal) =>
    requestJson(ChunkListSchema, { url: API_ROUTES.KB_CHUNKS(kbId, docId), method: 'GET', signal }),

  createChunk: (kbId: string, docId: string, content: string) =>
    requestJson(KBChunkSchema, {
      url: API_ROUTES.KB_CHUNKS(kbId, docId), method: 'POST', data: { content },
    }),

  updateChunk: (kbId: string, chunkId: string, content: string) =>
    requestJson(KBChunkSchema, {
      url: API_ROUTES.KB_CHUNK(kbId, chunkId), method: 'PATCH', data: { content },
    }),

  deleteChunk: (kbId: string, chunkId: string) =>
    requestJson(z.any(), { url: API_ROUTES.KB_CHUNK(kbId, chunkId), method: 'DELETE' }),

  reindexDoc: (kbId: string, docId: string) =>
    requestJson(DocOutSchema, {
      url: API_ROUTES.KB_DOC_REINDEX(kbId, docId), method: 'POST',
    }),

  reindex: (kbId: string) =>
    requestJson(
      z.object({ reindexed: z.number(), needs_reupload: z.number(), message: z.string() }),
      { url: API_ROUTES.KB_REINDEX(kbId), method: 'POST' }
    ),
}

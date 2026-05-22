import { z } from 'zod'

export const KBDocumentSchema = z.object({
  id: z.string(),
  name: z.string(),
  source_type: z.enum(['text', 'file', 'url']),
  chunk_count: z.number(),
  status: z.string(),
  created_at: z.string(),
})
export type KBDocument = z.infer<typeof KBDocumentSchema>

export const KnowledgeBaseSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  embedding_model: z.string(),
  embedding_credential_id: z.string().nullable().optional(),
  document_count: z.number(),
  total_chunks: z.number(),
  min_chunk_size: z.number().optional(),
  max_chunk_tokens: z.number().optional(),
  overlap_tokens: z.number().optional(),
  chunking_strategy: z.string().optional(),
  created_at: z.string(),
})
export type KnowledgeBase = z.infer<typeof KnowledgeBaseSchema>

export const KBDetailSchema = KnowledgeBaseSchema.extend({
  documents: z.array(KBDocumentSchema),
})
export type KBDetail = z.infer<typeof KBDetailSchema>

export const SearchResultSchema = z.object({
  id: z.string(),
  content: z.string(),
  document_id: z.string(),
  chunk_index: z.number(),
  score: z.number(),
})
export type SearchResult = z.infer<typeof SearchResultSchema>

export const KBChunkSchema = z.object({
  id: z.string(),
  content: z.string(),
  chunk_index: z.number(),
  has_embedding: z.boolean(),
})
export type KBChunk = z.infer<typeof KBChunkSchema>

export const SearchResponseSchema = z.object({
  query: z.string(),
  results: z.array(SearchResultSchema),
  count: z.number(),
})

export interface KBCreateRequest {
  name: string
  description?: string
  embedding_model: string
  embedding_credential_id?: string | null
  min_chunk_size?: number    // chars
  max_chunk_tokens?: number  // tokens (server multiplies by 4)
  overlap_tokens?: number    // tokens
  chunking_strategy?: string
}

export const CHUNKING_STRATEGIES = [
  { id: 'auto',      label: 'Auto (detect from content)', desc: 'Auto detects the best strategy based on file content type.' },
  { id: 'fixed',     label: 'Fixed size',                 desc: 'Split into equal-size character chunks with overlap.' },
  { id: 'paragraph', label: 'Paragraph',                  desc: 'Split on blank lines, keeping paragraphs together.' },
  { id: 'sentence',  label: 'Sentence',                   desc: 'Split on sentence boundaries.' },
  { id: 'markdown',  label: 'Markdown headers',           desc: 'Split on # headings, keeping sections together.' },
]

export const EMBEDDING_MODELS = [
  // OpenAI
  { id: 'text-embedding-3-small', label: 'text-embedding-3-small', provider: 'OpenAI', credType: 'openai_api_key', dims: 1536 },
  { id: 'text-embedding-3-large', label: 'text-embedding-3-large', provider: 'OpenAI', credType: 'openai_api_key', dims: 3072 },
  { id: 'text-embedding-ada-002',  label: 'text-embedding-ada-002',  provider: 'OpenAI', credType: 'openai_api_key', dims: 1536 },
  // Google
  { id: 'text-embedding-004', label: 'text-embedding-004', provider: 'Google', credType: 'google_api_key', dims: 768 },
  // Mistral
  { id: 'mistral-embed', label: 'mistral-embed', provider: 'Mistral', credType: 'mistral_api_key', dims: 1024 },
]

export const EMBEDDING_PROVIDERS = ['OpenAI', 'Google', 'Mistral']

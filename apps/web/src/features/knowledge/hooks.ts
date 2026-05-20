import { useState, useEffect, useCallback } from 'react'
import apiClient from '@/lib/api/client'

export function useKnowledgeBases() {
  const [kbs, setKbs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const refetch = useCallback(async () => {
    setLoading(true)
    try {
      const res = await apiClient.get('/kb/')
      setKbs(res.data || [])
    } catch { }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { refetch() }, [refetch])
  return { kbs, loading, refetch }
}

export function useKBDocuments(kbId: string) {
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const refetch = useCallback(async () => {
    setLoading(true)
    try {
      const res = await apiClient.get(`/kb/${kbId}`)
      setDocuments(res.data.documents || [])
    } catch { }
    finally { setLoading(false) }
  }, [kbId])

  useEffect(() => { refetch() }, [refetch])
  return { documents, loading, refetch }
}

export function useKBSearch(kbId: string) {
  const [results, setResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)

  const search = useCallback(async (query: string, topK = 5) => {
    if (!query.trim()) return
    setSearching(true)
    try {
      const res = await apiClient.post(`/kb/${kbId}/search`, { query, top_k: topK })
      setResults(res.data.results || [])
    } catch { setResults([]) }
    finally { setSearching(false) }
  }, [kbId])

  return { results, searching, search }
}

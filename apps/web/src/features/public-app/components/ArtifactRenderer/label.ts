import type { Artifact } from '../../types/artifactTypes'

export function artifactLabel(a: Artifact): string {
  if (a.title) return a.title
  const tData = a.data as Record<string, unknown>
  const guess =
    (typeof tData?.filename === 'string' && tData.filename) ||
    (typeof tData?.title === 'string' && tData.title) ||
    (typeof tData?.url === 'string' && tData.url) ||
    a.type
  return String(guess)
}

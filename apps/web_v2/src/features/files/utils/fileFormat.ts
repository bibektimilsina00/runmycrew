import type { FileAsset } from '../types/filesTypes'

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  let value = bytes / 1024
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value >= 10 ? value.toFixed(0) : value.toFixed(1)} ${units[unitIndex]}`
}

export function fileExtension(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() || 'data'
  if (['pdf', 'csv', 'doc', 'docx', 'json', 'xls', 'xlsx'].includes(ext)) {
    return ext === 'docx' ? 'doc' : ext === 'xlsx' ? 'xls' : ext
  }
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) return 'img'
  return 'data'
}

export function sourceLabel(source: FileAsset['source_type']): string {
  if (source === 'generated') return 'Agent output'
  if (source === 'attachment') return 'Attachment'
  return 'Manual upload'
}

export function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime()
  const mins = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return new Date(isoString).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

import { useMemo, useRef, useState } from 'react'
import { Icons } from '@/shared/components/icons'
import { useConfirm, useToast } from '@/shared/components'
import { filesAPI } from '../services/filesAPI'
import { useDeleteFile, useFiles, useFileStats, useUploadFile } from '../hooks/useFiles'
import { FilesList } from '../components/FilesList'
import type { FileAsset, FileFilter, FileSort } from '../types/filesTypes'
import { formatBytes } from '../utils/fileFormat'

const FILTERS: { id: FileFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'generated', label: 'Generated' },
  { id: 'uploaded', label: 'Uploaded' },
  { id: 'attachments', label: 'Attachments' },
]

export function Files() {
  const { toast } = useToast()
  const confirm = useConfirm()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { data: items = [], isLoading } = useFiles()
  const { data: stats } = useFileStats()
  const uploadFile = useUploadFile()
  const deleteFile = useDeleteFile()
  const [filter, setFilter] = useState<FileFilter>('all')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<FileSort>('created_desc')

  const visibleItems = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    const filtered = items.filter(file => {
      const matchesFilter =
        filter === 'all' ||
        file.source_type === filter ||
        (filter === 'attachments' && file.source_type === 'attachment')
      const matchesSearch =
        !normalizedSearch ||
        file.name.toLowerCase().includes(normalizedSearch) ||
        file.file_type.toLowerCase().includes(normalizedSearch)
      return matchesFilter && matchesSearch
    })

    return [...filtered].sort((a, b) => {
      if (sort === 'name_asc') return a.name.localeCompare(b.name)
      if (sort === 'size_desc') return b.file_size - a.file_size
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
  }, [filter, items, search, sort])

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    let uploaded = 0
    for (const file of Array.from(files)) {
      try {
        await uploadFile.mutateAsync(file)
        uploaded += 1
      } catch {
        toast(`Failed to upload ${file.name}`, { variant: 'err' })
      }
    }
    if (uploaded > 0) {
      toast(`${uploaded} file${uploaded === 1 ? '' : 's'} uploaded`, { variant: 'ok' })
    }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleOpen = async (file: FileAsset) => {
    try {
      const blob = await filesAPI.viewBlob(file.id)
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener')
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch {
      toast('Failed to open file', { variant: 'err' })
    }
  }

  const handleDelete = async (file: FileAsset) => {
    const ok = await confirm({
      title: 'Delete file',
      message: `Delete "${file.name}"? This cannot be undone.`,
      confirmText: 'Delete',
      variant: 'danger',
    })
    if (!ok) return
    try {
      await deleteFile.mutateAsync(file.id)
      toast('File deleted', { variant: 'ok' })
    } catch {
      toast('Failed to delete file', { variant: 'err' })
    }
  }

  const cycleSort = () => {
    setSort(current => {
      if (current === 'created_desc') return 'name_asc'
      if (current === 'name_asc') return 'size_desc'
      return 'created_desc'
    })
  }

  return (
    <div className="view-body min-h-full">
      <div className="page-head">
        <div>
          <span className="eyebrow">
            Workspace · {stats?.count ?? items.length} files · {formatBytes(stats?.total_size ?? totalSize(items))} used
          </span>
          <h1>Files</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={() => toast('Folders are not available for files yet', { variant: 'warn' })}>
            <Icons.Folder /> New folder
          </button>
          <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()} disabled={uploadFile.isPending}>
            <Icons.Plus /> {uploadFile.isPending ? 'Uploading...' : 'Upload'}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={event => handleUpload(event.target.files)}
          />
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {FILTERS.map(item => (
            <button key={item.id} className={`filter-tab${filter === item.id ? ' active' : ''}`} onClick={() => setFilter(item.id)}>
              {item.label}
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icons.Search />
            <input placeholder="Search files" value={search} onChange={event => setSearch(event.target.value)} />
          </div>
          <button className="icon-btn" title={`Sort: ${sortLabel(sort)}`} onClick={cycleSort}><Icons.Sort /></button>
        </div>
      </div>

      <FilesList
        items={visibleItems}
        totalCount={items.length}
        isLoading={isLoading}
        onOpen={handleOpen}
        onDelete={handleDelete}
      />
    </div>
  )
}

function totalSize(items: FileAsset[]): number {
  return items.reduce((sum, item) => sum + item.file_size, 0)
}

function sortLabel(sort: FileSort): string {
  if (sort === 'name_asc') return 'Name'
  if (sort === 'size_desc') return 'Size'
  return 'Newest'
}

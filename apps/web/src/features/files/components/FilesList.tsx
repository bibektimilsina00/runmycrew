import { Empty } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import type { FileAsset } from '../types/filesTypes'
import { fileExtension, formatBytes, sourceLabel, timeAgo } from '../utils/fileFormat'

interface Props {
  items: FileAsset[]
  totalCount?: number
  isLoading?: boolean
  onOpen: (file: FileAsset) => void
  onDelete: (file: FileAsset) => void
}

export function FilesList({ items, totalCount = 0, isLoading, onOpen, onDelete }: Props) {
  if (isLoading) {
    return (
      <div className="panel">
        <Empty
          icon={<Icons.Folder />}
          title="Loading files…"
          className="flex-1 justify-center"
        />
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="panel">
        <Empty
          icon={<Icons.Folder />}
          title="No files found"
          description={
            totalCount === 0
              ? 'Upload files to make them available in this workspace.'
              : 'No files match the current filter.'
          }
          className="flex-1 justify-center"
        />
      </div>
    )
  }

  return (
    <div className="panel">
      <div className="table table-files">
        <div className="table-head">
          <span></span>
          <span>Name</span>
          <span>Size</span>
          <span>Source</span>
          <span>Uploaded</span>
          <span></span>
        </div>
        {items.map(file => (
          <div key={file.id} className="table-row text-left" onClick={() => onOpen(file)}>
            <span className={`file-icon ${fileExtension(file.name)}`}>{fileExtension(file.name).toUpperCase()}</span>
            <span className="row-name">{file.name}</span>
            <span className="row-mono">{formatBytes(file.file_size)}</span>
            <span className="row-owner">{sourceLabel(file.source_type)}</span>
            <span className="row-mono">{timeAgo(file.created_at)}</span>
            <span className="caret">
              <button
                type="button"
                title="Delete file"
                onClick={e => { e.stopPropagation(); onDelete(file) }}
                className="w-[20px] h-[20px] inline-flex items-center justify-center text-[var(--text-faint)] hover:text-[var(--err)]"
              >
                <Icons.Trash />
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

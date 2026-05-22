import { Empty } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import type { FileAsset } from '../types/filesTypes'
import { fileExtension, formatBytes, sourceLabel, timeAgo } from '../utils/fileFormat'

interface Props {
  items: FileAsset[]
  isLoading?: boolean
  onOpen: (file: FileAsset) => void
  onDelete: (file: FileAsset) => void
}

export function FilesList({ items, isLoading, onOpen, onDelete }: Props) {
  return (
    <div className="panel flex-1 min-h-0 flex flex-col">
      <div className="table table-files flex-1 min-h-0">
        <div className="table-head">
          <span></span>
          <span>Name</span>
          <span>Size</span>
          <span>Source</span>
          <span>Uploaded</span>
          <span></span>
        </div>
        {isLoading ? (
          <div className="table-row">
            <span></span>
            <span className="row-owner">Loading files...</span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>
        ) : items.length === 0 ? (
          <div className="flex-1 min-h-[360px] border-b border-[var(--border-faint)] flex items-center justify-center">
            <Empty
              icon={<Icons.Folder />}
              title="No files found"
              description="Upload files to make them available in this workspace."
              className="py-10"
            />
          </div>
        ) : (
          items.map(file => (
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
                  onClick={event => {
                    event.stopPropagation()
                    onDelete(file)
                  }}
                  className="w-[20px] h-[20px] inline-flex items-center justify-center text-[var(--text-faint)] hover:text-[var(--err)]"
                >
                  <Icons.Trash />
                </button>
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

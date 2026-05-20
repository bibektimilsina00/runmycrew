import React from 'react'
import { Search, Plus, BookOpen, History, Pencil } from 'lucide-react'
import { IconButton } from '@/components/ui'
import { getIcon } from '@/features/workflow-editor/utils/icon-map'
import { useUIStore, type InspectorTabType } from '@/stores/ui-store'

interface NodeHeaderProps {
  activeTab: InspectorTabType
  selectedNode: any
  definition: any
  isEditingName: boolean
  editNameValue: string
  onEditNameChange: (val: string) => void
  onEditClick: () => void
  onNameSave: () => void
}

export const NodeHeader: React.FC<NodeHeaderProps> = ({
  activeTab, selectedNode, definition, isEditingName, editNameValue, onEditNameChange, onEditClick, onNameSave,
}) => {
  const showNodeInfo = activeTab === 'Editor' && selectedNode && definition
  const { copilotView, setCopilotView, triggerCopilotNewChat } = useUIStore()

  return (
    <div className="flex items-center justify-between px-4 py-2.5 mt-2 border-y border-[var(--border-default)] min-h-[45px]">
      <div className="flex items-center gap-2.5 min-w-0 flex-1 mr-2">
        {showNodeInfo ? (
          <>
            <div
              className="flex size-5 items-center justify-center rounded-md flex-shrink-0"
              style={{ backgroundColor: definition.color || '#3b82f6' }}
            >
              {React.cloneElement(getIcon(definition.icon) as React.ReactElement, { className: 'size-3 text-white' })}
            </div>
            {isEditingName ? (
              <input
                autoFocus
                value={editNameValue}
                onChange={(e) => onEditNameChange(e.target.value)}
                onBlur={onNameSave}
                onKeyDown={(e) => e.key === 'Enter' && onNameSave()}
                className="bg-surface-editor rounded px-1.5 py-0.5 text-[13px] font-bold text-white w-full focus:outline-none border-none"
              />
            ) : (
              <span
                onDoubleClick={onEditClick}
                className="text-[13px] font-bold text-white tracking-tight truncate cursor-pointer hover:text-gray-300 transition-colors"
              >
                {selectedNode.data.label || definition.name}
              </span>
            )}
          </>
        ) : (
          <span className="text-[13px] font-bold text-white tracking-tight">
            {activeTab === 'Copilot' ? 'New Chat' : activeTab === 'Toolbar' ? 'Toolbar' : activeTab.toUpperCase()}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1 flex-shrink-0">
        {activeTab === 'Copilot' && (
          <>
            <IconButton icon={<Plus />} tooltip="New chat" size="sm" onClick={triggerCopilotNewChat} />
            <IconButton
              icon={<History />}
              tooltip="Chat history"
              size="sm"
              onClick={() => setCopilotView(copilotView === 'history' ? 'chat' : 'history')}
            />
          </>
        )}
        {activeTab === 'Toolbar' && (
          <IconButton icon={<Search />} tooltip="Search nodes" size="sm" />
        )}
        {activeTab === 'Editor' && (
          <>
            {!isEditingName && selectedNode && (
              <IconButton icon={<Pencil />} tooltip="Rename node" size="sm" onClick={onEditClick} />
            )}
            <IconButton icon={<BookOpen />} tooltip="Open documentation" size="sm" />
          </>
        )}
      </div>
    </div>
  )
}

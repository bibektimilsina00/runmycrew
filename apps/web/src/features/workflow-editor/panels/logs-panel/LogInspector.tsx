import React, { useState, useRef, useEffect, useMemo } from 'react'
import {
  Search,
  Clipboard,
  ArrowDownToLine,
  Trash2,
  Ellipsis,
  ChevronDown,
  X,
} from 'lucide-react'
import Editor from 'react-simple-code-editor'
import Prism from 'prismjs'
;(globalThis as any).Prism = Prism
import('prismjs/components/prism-json')
import { cn } from '@/lib/utils'
import { ToolbarButton, OptionItem, DataNode } from '@/features/workflow-editor/components/common/EditorUI'
import { useExecutionStore } from '@/stores/execution-store'
import { useUIStore } from '@/stores/ui-store'
import { useClickOutside } from '@/features/workflow-editor/hooks/use-click-outside'
import { getLogDisplayData, filterLogNodes, getAvailableTabs } from '@/features/workflow-editor/panels/logs-panel/log-utils'

type TabType = 'Output' | 'Input'

interface LogInspectorProps {
  isCollapsed: boolean
  toggleCollapse: () => void
}

export const LogInspector = React.memo(({
  isCollapsed,
  toggleCollapse,
}: LogInspectorProps) => {
  const { runs, selectedLogId, clearRuns } = useExecutionStore()
  const { logViewMode, setLogViewMode, logWrapView, setLogWrapView, logOpenOnRun, setLogOpenOnRun } = useUIStore()

  // Transient UI state (not worth persisting)
  const [activeTab, setActiveTab] = useState<TabType>('Output')
  const [showOptions, setShowOptions] = useState(false)
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const optionsRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  useClickOutside(optionsRef, () => setShowOptions(false))

  useEffect(() => {
    if (isSearchOpen) {
      setTimeout(() => searchInputRef.current?.focus(), 50)
    }
  }, [isSearchOpen])

  // Find selected log across all runs
  const selectedLog = useMemo(() => {
    if (!selectedLogId) return null
    for (const run of runs) {
      const log = run.logs.find((l) => l.id === selectedLogId)
      if (log) return log
    }
    return null
  }, [selectedLogId, runs])

  const availableTabs = useMemo(
    () => getAvailableTabs(selectedLog),
    [selectedLog]
  )

  // Auto-switch to a valid tab when selection changes
  useEffect(() => {
    if (!availableTabs.includes(activeTab)) {
      setActiveTab(availableTabs[0] ?? 'Output')
    }
  }, [availableTabs, activeTab])

  const displayData = useMemo(
    () => getLogDisplayData(selectedLog, activeTab),
    [selectedLog, activeTab]
  )

  const filteredNodes = useMemo(
    () => filterLogNodes(displayData, searchQuery),
    [displayData, searchQuery]
  )

  const jsonString = JSON.stringify(displayData ?? {}, null, 2)
  const isStructured = logViewMode === 'structured'
  const interpolationNodeId = activeTab === 'Output' ? selectedLog?.node_id : null

  return (
    <>
      <div className="w-px flex-shrink-0 bg-[var(--border-default)]" />

      <div
        className="flex flex-col bg-[var(--bg)] h-full overflow-hidden flex-shrink-0"
        style={{ width: '70%' }}
      >
        {/* Toolbar */}
        <div className="flex h-[30px] flex-shrink-0 items-center justify-between bg-[var(--bg)] px-4 border-b border-transparent">
          <div className="flex items-center">
            {availableTabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'px-2 py-1 text-[12px] font-bold transition-all',
                  activeTab === tab ? 'text-white' : 'text-[var(--text-icon)] hover:text-[var(--text-primary)]'
                )}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-0.5">
            {isSearchOpen ? (
              <div className="flex items-center bg-[var(--surface-1)] rounded px-1.5 py-0.5 border border-[var(--border-default)] h-[22px] mr-1 animate-in fade-in slide-in-from-right-2 duration-200">
                <Search className="size-3 text-[var(--text-muted)] mr-1.5" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search..."
                  className="bg-transparent border-none outline-none text-[10px] text-white w-28 placeholder:text-[var(--text-muted)]"
                  onKeyDown={(e) => e.key === 'Escape' && setIsSearchOpen(false)}
                />
                <button onClick={() => { setIsSearchOpen(false); setSearchQuery('') }}>
                  <X className="size-2.5 text-[var(--text-muted)] hover:text-white" />
                </button>
              </div>
            ) : (
              <ToolbarButton icon={<Search className="size-3.5" />} label="Search" onClick={() => setIsSearchOpen(true)} />
            )}

            <ToolbarButton
              icon={<Clipboard className="size-3.5" />}
              label="Copy"
              onClick={() => navigator.clipboard.writeText(jsonString)}
            />
            <ToolbarButton icon={<ArrowDownToLine className="size-3.5" />} label="Download" />
            <ToolbarButton icon={<Trash2 className="size-3.5" />} label="Clear logs" onClick={clearRuns} />
            <div className="w-[1px] h-3 bg-[var(--border-default)] mx-1" />

            <div className="relative flex items-center" ref={optionsRef}>
              <ToolbarButton
                icon={<Ellipsis className="size-3.5" />}
                label="Options"
                onClick={() => setShowOptions((v) => !v)}
              />
              {showOptions && (
                <div className="absolute right-0 top-full mt-1 w-36 rounded-lg bg-[var(--surface-1)] border border-[var(--border-default)] shadow-xl z-[100] py-1 animate-in fade-in slide-in-from-top-2 duration-150">
                  <OptionItem
                    label="Structured View"
                    checked={isStructured}
                    onClick={() => { setLogViewMode(isStructured ? 'raw' : 'structured'); setShowOptions(false) }}
                  />
                  <OptionItem
                    label="Wrap Text"
                    checked={logWrapView}
                    onClick={() => { setLogWrapView(!logWrapView); setShowOptions(false) }}
                  />
                  <div className="my-1 border-t border-[var(--border-default)]" />
                  <OptionItem
                    label="Open on Run"
                    checked={logOpenOnRun}
                    onClick={() => { setLogOpenOnRun(!logOpenOnRun); setShowOptions(false) }}
                  />
                </div>
              )}
            </div>

            <ToolbarButton
              icon={<ChevronDown className={cn('size-3.5 transition-transform duration-200', isCollapsed && 'rotate-180')} />}
              label={isCollapsed ? 'Expand' : 'Collapse'}
              onClick={toggleCollapse}
            />
          </div>
        </div>

        {/* Content */}
        <div className={cn('flex-1 overflow-y-auto custom-scrollbar p-5', isCollapsed && 'hidden')}>
          {!selectedLog ? (
            <div className="flex h-full items-center justify-center text-[var(--text-muted)] text-[12px] italic">
              Select a log entry to view details
            </div>
          ) : isStructured ? (
            <div className="flex flex-col gap-2 overflow-hidden">
              {filteredNodes.length > 0 ? (
                filteredNodes.map((node, i) => (
                  <DataNode
                    key={node.label + i}
                    label={node.label}
                    value={node.value}
                    initialCollapsed={false}
                    interpolationNodeId={interpolationNodeId ?? undefined}
                    interpolationPath={interpolationNodeId ? [node.label] : undefined}
                  />
                ))
              ) : (
                <div className="text-[var(--text-muted)] text-[12px] italic">
                  {Object.keys(displayData ?? {}).length === 0
                    ? `No ${activeTab.toLowerCase()} data for this step`
                    : `No matches for "${searchQuery}"`}
                </div>
              )}
            </div>
          ) : (
            <div className={cn('h-full w-full', logWrapView ? 'whitespace-pre-wrap' : 'whitespace-pre')}>
              <Editor
                value={jsonString}
                onValueChange={() => {}}
                highlight={(code) => Prism.highlight(code, Prism.languages.json, 'json')}
                padding={0}
                className="prism-editor"
                style={{ fontFamily: '"Fira code", "Fira Mono", monospace', fontSize: 13 }}
                readOnly
              />
            </div>
          )}
        </div>
      </div>
    </>
  )
})

import { useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  Copy, Download, WrapText, MoreVertical, Search, X,
  Maximize2, Minimize2, SlidersHorizontal, Braces, ListTree, FileJson2,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import { useWorkflowEditorStore } from '../../../../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../../../../stores/editorLayoutStore'
import { IconBtn } from './IconBtn'
import { OverflowMenu, type OverflowItem } from './OverflowMenu'
import { JsonCodeView } from './JsonCodeView'
import { JsonTreeView, type Reference } from './JsonTreeView'
import { stringifyJson } from './json-utils'
import { StructuredErrorCard } from './StructuredErrorCard'
import { parseStructuredError } from './structuredError'
import type { Tab, ViewMode } from './types'

interface Props {
  payload: unknown
  nodeId: string | null
  /**
   * Display label of the source node — when provided, drag-drop emits
   * `=$node('Label').path` so dropped refs survive node renames better
   * than raw ids. Falls back to the raw `nodeId` when omitted.
   */
  nodeLabel?: string | null
  /** When provided, renders a header row with Output/Input tabs. */
  tab?: Tab
  onTabChange?: (tab: Tab) => void
  /** Filename stem used when the user downloads the JSON (default: `nodeId`). */
  downloadName?: string
  /** Extra label shown in the header when no tab row is rendered. */
  title?: string
  /** Optional banner rendered between the toolbar/search row and the body. */
  headerBanner?: React.ReactNode
  /** Optional row rendered below the body — e.g. action buttons. */
  footer?: React.ReactNode
  /**
   * When set, replaces the default tree/code body. Callers use this to
   * render a fully bespoke body (e.g. the structured-error card) while
   * keeping the inspector's toolbar, header banner, and footer. The
   * toolbar's view-mode toggle and search still affect the underlying
   * payload, so they're hidden when an override is active.
   */
  bodyOverride?: React.ReactNode
}

/**
 * Generic JSON inspector — toolbar (Copy / Download / Wrap / More) plus a
 * body that switches between a collapsible tree and a syntax-highlighted
 * code view. Can render with or without the Output/Input tabs.
 *
 * Fullscreen mode portals the inspector into a backdrop-dimmed modal.
 */
export function JsonInspector({
  payload,
  nodeId,
  nodeLabel,
  tab,
  onTabChange,
  downloadName,
  title,
  headerBanner,
  footer,
  bodyOverride,
}: Props) {
  // Without a known label we don't have a stable reference style — leave the
  // tree non-draggable rather than emit a raw-uuid form the rest of the
  // system no longer accepts.
  const treeReference: Reference | null = nodeLabel
    ? { kind: 'label', label: nodeLabel }
    : null
  const [view, setView] = useState<ViewMode>('tree')
  const [wrap, setWrap] = useState(true)
  const [pretty, setPretty] = useState(true)
  const [searchActive, setSearchActive] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [fullscreen, setFullscreen] = useState(false)
  const [menuRect, setMenuRect] = useState<DOMRect | null>(null)
  const menuBtnRef = useRef<HTMLButtonElement>(null)

  const empty = payload === null || payload === undefined

  // Auto-detect a structured error payload anywhere in the inspector
  // chain — the backend emits these as sentinel-prefixed strings, and
  // we want the polished card to show up wherever the inspector ends
  // up rendering one (LogsPanel's output tab, listen-mode preview,
  // sub-workflow error pass-through, etc) without each call site
  // having to remember the override.
  const autoStructured = useMemo(() => {
    const direct = parseStructuredError(payload)
    if (direct) return direct
    // Also handle the common case where the caller passes the whole
    // payload object and the sentinel lives under `.error`.
    if (payload && typeof payload === 'object' && 'error' in payload) {
      return parseStructuredError((payload as Record<string, unknown>).error)
    }
    return null
  }, [payload])

  const codeSource = useMemo(() => stringifyJson(payload, pretty), [payload, pretty])

  const visibleCode = useMemo(() => {
    if (!searchActive || !searchQuery.trim()) return codeSource
    const q = searchQuery.toLowerCase()
    return codeSource
      .split('\n')
      .filter((line) => line.toLowerCase().includes(q))
      .join('\n')
  }, [codeSource, searchActive, searchQuery])

  const copyJson = () => { void navigator.clipboard.writeText(codeSource) }
  const copyNodeId = () => { if (nodeId) void navigator.clipboard.writeText(nodeId) }
  const downloadJson = () => {
    const blob = new Blob([codeSource], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${downloadName ?? nodeId ?? 'log'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
  const openInspector = () => {
    if (!nodeId) return
    useWorkflowEditorStore.getState().setSelectedNodeId(nodeId)
    useEditorLayoutStore.getState().focusTab('config')
  }
  const openMenu = () => setMenuRect(menuBtnRef.current?.getBoundingClientRect() ?? null)
  const closeMenu = () => setMenuRect(null)

  const overflowItems: OverflowItem[] = [
    {
      label: view === 'tree' ? 'Switch to JSON view' : 'Switch to tree view',
      icon: view === 'tree' ? <FileJson2 /> : <ListTree />,
      onClick: () => setView((v) => (v === 'tree' ? 'code' : 'tree')),
      disabled: empty,
    },
    {
      label: pretty ? 'Show raw JSON' : 'Show pretty JSON',
      icon: <Braces />,
      onClick: () => setPretty((p) => !p),
      disabled: empty || view !== 'code',
    },
    {
      label: searchActive ? 'Close search' : 'Search in JSON',
      icon: <Search />,
      onClick: () => setSearchActive((s) => !s),
      disabled: empty || view !== 'code',
    },
    {
      label: 'Copy nodeId',
      icon: <Copy />,
      onClick: copyNodeId,
      disabled: !nodeId,
      dividerBefore: true,
    },
    {
      label: 'Open node in Inspector',
      icon: <SlidersHorizontal />,
      onClick: openInspector,
      disabled: !nodeId,
    },
    {
      label: fullscreen ? 'Exit fullscreen' : 'Fullscreen',
      icon: fullscreen ? <Minimize2 /> : <Maximize2 />,
      onClick: () => setFullscreen((f) => !f),
      dividerBefore: true,
    },
  ]

  const body = (
    <div className="flex h-full min-h-0 flex-col">
      {/* Header */}
      <div className="flex h-[36px] shrink-0 items-center gap-1 border-b border-[var(--border-faint)] px-3">
        {tab && onTabChange ? (
          (['output', 'input'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => onTabChange(t)}
              className={cn(
                'rounded-[6px] px-2 py-1 text-[11.5px] capitalize transition-colors',
                tab === t
                  ? 'bg-[var(--surface-2)] text-[var(--text)]'
                  : 'text-[var(--text-mute)] hover:text-[var(--text)]',
              )}
            >
              {t}
            </button>
          ))
        ) : title ? (
          <span className="px-1 text-[11.5px] font-medium text-[var(--text)]">{title}</span>
        ) : null}

        <div className="ml-auto flex items-center gap-0.5">
          <IconBtn
            icon={view === 'tree' ? <FileJson2 className="h-3.5 w-3.5" /> : <ListTree className="h-3.5 w-3.5" />}
            title={view === 'tree' ? 'Switch to JSON view' : 'Switch to tree view'}
            onClick={() => setView((v) => (v === 'tree' ? 'code' : 'tree'))}
            disabled={empty}
          />
          <IconBtn
            icon={<Copy className="h-3.5 w-3.5" />}
            title="Copy JSON"
            onClick={copyJson}
            disabled={empty}
          />
          <IconBtn
            icon={<Download className="h-3.5 w-3.5" />}
            title="Download .json"
            onClick={downloadJson}
            disabled={empty}
          />
          <IconBtn
            icon={<WrapText className="h-3.5 w-3.5" />}
            title={wrap ? 'Disable wrap' : 'Wrap lines'}
            onClick={() => setWrap((w) => !w)}
            active={wrap}
            disabled={empty || view !== 'code'}
          />
          <IconBtn
            icon={<MoreVertical className="h-3.5 w-3.5" />}
            title="More"
            onClick={openMenu}
            btnRef={menuBtnRef}
          />
        </div>
      </div>

      {/* Search bar */}
      {searchActive && view === 'code' && (
        <div className="flex shrink-0 items-center gap-2 border-b border-[var(--border-faint)] bg-[var(--surface)] px-3 py-1.5">
          <Search className="h-3.5 w-3.5 text-[var(--text-faint)]" />
          <input
            autoFocus
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter lines…"
            className="flex-1 bg-transparent text-[11.5px] text-[var(--text)] outline-none placeholder:text-[var(--text-faint)]"
          />
          <button
            onClick={() => { setSearchActive(false); setSearchQuery('') }}
            className="text-[var(--text-faint)] transition-colors hover:text-[var(--text)]"
            title="Close search"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Optional banner (e.g. ErrorView headline) */}
      {headerBanner}

      {/* Body — three render paths in priority order:
          1. Caller-supplied `bodyOverride` (e.g. ErrorView for a known
             failed log; lets the caller customise the headline too).
          2. Auto-detected structured-error payload — anywhere in the
             app that hands a sentinel-prefixed string to the inspector,
             we surface the polished card automatically.
          3. Default tree / code view. */}
      {bodyOverride !== undefined ? (
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">{bodyOverride}</div>
      ) : autoStructured ? (
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <StructuredErrorCard data={autoStructured} />
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-auto px-3 py-2 text-left">
          {empty ? (
            <div className="text-[var(--text-faint)] italic font-mono text-[11.5px]">
              No data available.
            </div>
          ) : view === 'tree' ? (
            <JsonTreeView value={payload} reference={treeReference} />
          ) : (
            <JsonCodeView source={visibleCode} wrap={wrap} />
          )}
        </div>
      )}

      {/* Optional footer (e.g. ErrorView action buttons) */}
      {footer}

      {menuRect && (
        <OverflowMenu anchorRect={menuRect} items={overflowItems} onClose={closeMenu} />
      )}
    </div>
  )

  if (fullscreen) {
    return createPortal(
      <div className="fixed inset-0 z-[9990] flex items-stretch bg-[oklch(0_0_0/0.55)] p-6 backdrop-blur-sm">
        <div className="flex h-full w-full flex-col overflow-hidden rounded-[12px] border border-[var(--border-faint)] bg-[var(--bg-2)] shadow-[0_24px_60px_-20px_oklch(0_0_0/0.7)]">
          {body}
        </div>
      </div>,
      document.body,
    )
  }
  return body
}

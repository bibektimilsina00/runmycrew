import { AlertOctagon, Sparkles, SlidersHorizontal, Copy } from 'lucide-react'
import type { RunLog } from '@/features/runs/store/runsStore'
import { useWorkflowEditorStore } from '../../../../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../../../../stores/editorLayoutStore'
import { JsonInspector } from './JsonInspector'
import { StructuredErrorCard } from './StructuredErrorCard'
import { parseStructuredError } from './structuredError'
import { stringifyJson } from './json-utils'
import type { NodeInfo, Tab } from './types'

interface Props {
  log: RunLog
  nodeInfo: NodeInfo
  tab: Tab
  onTabChange: (t: Tab) => void
}

/**
 * Failed-node view: renders the standard `JsonInspector` for the error
 * payload so the Output/Input tab row and the toolbar stay at the same Y
 * position they do for successful nodes. The error headline drops in as
 * `headerBanner` (between toolbar and body) and the action buttons drop in
 * as `footer` — `JsonInspector` owns the layout.
 */
export function ErrorView({ log, nodeInfo, tab, onTabChange }: Props) {
  const rawError = log.payload?.error
  const errorText = stringifyJson(rawError, true)

  // Nodes can opt into a structured error payload (title + summary +
  // bulleted actions + collapsible raw response) via the sentinel
  // prefix emitted by `make_structured_error` on the backend. Falls
  // back to the legacy headline + JSON tree for anything else.
  const structured = parseStructuredError(rawError)

  const headline =
    structured?.title ||
    (typeof rawError === 'object' && rawError && 'message' in rawError
      ? String((rawError as { message?: unknown }).message ?? '')
      : '') ||
    (typeof rawError === 'string' ? rawError : '') ||
    'Node execution failed'

  const fixWithCopilot = () => {
    if (!log.nodeId) return
    useWorkflowEditorStore.getState().setSelectedNodeId(log.nodeId)
    useEditorLayoutStore.getState().focusTab('copilot')
    const detail = {
      message:
        `Fix the "${nodeInfo.label}" node. It failed with:\n\n` +
        '```\n' + errorText.slice(0, 1200) + '\n```',
    }
    setTimeout(
      () => window.dispatchEvent(new CustomEvent('copilot-send-message', { detail })),
      80,
    )
  }
  const inspectNode = () => {
    if (!log.nodeId) return
    useWorkflowEditorStore.getState().setSelectedNodeId(log.nodeId)
    useEditorLayoutStore.getState().focusTab('config')
  }
  const copyError = () => { void navigator.clipboard.writeText(errorText) }

  // Inspector body — structured card when the backend opted in,
  // raw JSON tree otherwise. The header banner + footer wrap both
  // paths identically so the toolbar stays put across error styles.
  const body = structured ? <StructuredErrorCard data={structured} /> : undefined

  return (
    <JsonInspector
      payload={rawError ?? {}}
      nodeId={log.nodeId}
      tab={tab}
      onTabChange={onTabChange}
      downloadName={`${log.nodeId || 'error'}-error`}
      bodyOverride={body}
      headerBanner={
        <div className="flex shrink-0 items-start gap-2.5 border-b border-[var(--border-faint)] bg-[rgba(239,68,68,0.06)] px-3 py-2.5">
          <AlertOctagon className="mt-[1px] h-4 w-4 shrink-0 text-[var(--err)]" />
          <div className="min-w-0 flex-1">
            <div className="text-[12px] font-semibold text-[var(--text)]">
              {nodeInfo.label} failed
            </div>
            <div className="mt-0.5 truncate text-[11px] text-[var(--text-mute)]" title={headline}>
              {headline}
            </div>
          </div>
        </div>
      }
      footer={
        <div className="flex shrink-0 items-center gap-1.5 border-t border-[var(--border-faint)] px-2 py-2">
          <button
            onClick={fixWithCopilot}
            disabled={!log.nodeId}
            className="inline-flex items-center gap-1.5 rounded-[7px] bg-[var(--text)] px-2.5 py-1.5 text-[11.5px] font-medium text-[var(--bg)] transition-colors hover:opacity-90 disabled:opacity-40"
          >
            <Sparkles className="h-3.5 w-3.5" /> Fix with Copilot
          </button>
          <button
            onClick={inspectNode}
            disabled={!log.nodeId}
            className="inline-flex items-center gap-1.5 rounded-[7px] px-2.5 py-1.5 text-[11.5px] font-medium text-[var(--text-mute)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)] disabled:opacity-40"
          >
            <SlidersHorizontal className="h-3.5 w-3.5" /> Inspect node
          </button>
          <button
            onClick={copyError}
            className="ml-auto inline-flex items-center gap-1.5 rounded-[7px] px-2.5 py-1.5 text-[11.5px] font-medium text-[var(--text-mute)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          >
            <Copy className="h-3.5 w-3.5" /> Copy
          </button>
        </div>
      }
    />
  )
}

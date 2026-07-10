import { AlertOctagon, Bot, SlidersHorizontal, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import type { RunLog } from '@/features/runs/store/runsStore'
import { useWorkflowEditorStore } from '../../../../stores/workflowEditorStore'
import { useEditorLayoutStore } from '../../../../stores/editorLayoutStore'
import { JsonInspector } from './JsonInspector'
import { StructuredErrorCard } from './StructuredErrorCard'
import { parseStructuredError, type StructuredError } from './structuredError'
import { stringifyJson } from './json-utils'
import type { NodeInfo, Tab } from './types'

interface Props {
  log: RunLog
  nodeInfo: NodeInfo
  tab: Tab
  onTabChange: (t: Tab) => void
}

/** Pull the human message out of whatever shape the error payload has. */
function extractMessage(raw: unknown): string {
  if (typeof raw === 'string') return raw
  if (raw && typeof raw === 'object' && 'message' in raw) {
    const m = (raw as { message?: unknown }).message
    if (typeof m === 'string' && m) return m
  }
  return ''
}

/** Presentational hints for the most common failure families. */
function actionsFor(message: string): string[] {
  const m = message.toLowerCase()
  if (m.includes('credential') || m.includes('api key') || m.includes('unauthorized') || m.includes('401')) {
    return [
      'Open the node and pick a credential in its Credential field.',
      'No credential yet? Connect one under Settings → Integrations.',
    ]
  }
  if (m.includes('rate limit') || m.includes('429')) {
    return ['The provider is throttling requests — wait a moment and run again.']
  }
  if (m.includes('timeout') || m.includes('timed out')) {
    return ['Increase the node’s timeout in Advanced Settings, or simplify the request.']
  }
  if (m.includes('not found') || m.includes('404')) {
    return ['Check the resource id / URL configured on this node — the target no longer exists.']
  }
  return []
}

/**
 * Failed-node view. Structured payloads (backend sentinel) render the
 * StructuredErrorCard directly. Plain errors get the SAME card,
 * synthesized: message as the headline, suggested next steps, and the
 * raw payload folded away — never a bare JSON dump duplicating the
 * banner. The slim banner keeps the node identity; the card owns the
 * message.
 */
export function ErrorView({ log, nodeInfo, tab, onTabChange }: Props) {
  const rawError = log.payload?.error
  const errorText = stringifyJson(rawError, true)
  const [copied, setCopied] = useState(false)

  const structured = parseStructuredError(rawError)

  const message = extractMessage(rawError)
  const synthesized: StructuredError | null = structured
    ? null
    : {
        title: message || 'Node execution failed',
        summary: '',
        actions: actionsFor(message),
        // Only offer the raw payload when it carries more than the
        // message we're already showing.
        raw:
          typeof rawError === 'object' && rawError && Object.keys(rawError).length > 1
            ? errorText
            : '',
        severity: 'error',
      }

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
  const copyError = () => {
    void navigator.clipboard.writeText(errorText)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <JsonInspector
      payload={rawError ?? {}}
      nodeId={log.nodeId}
      tab={tab}
      onTabChange={onTabChange}
      downloadName={`${log.nodeId || 'error'}-error`}
      bodyOverride={<StructuredErrorCard data={structured ?? synthesized!} />}
      headerBanner={
        <div className="flex shrink-0 items-center gap-2.5 border-b border-[var(--border-faint)] bg-[rgba(239,68,68,0.05)] px-3 py-2">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[7px] bg-[rgba(239,68,68,0.12)]">
            <AlertOctagon className="h-3.5 w-3.5 text-[var(--err)]" />
          </span>
          <span className="min-w-0 truncate text-[12.5px] font-semibold text-[var(--text)]">
            {nodeInfo.label} failed
          </span>
          {log.nodeId && (
            <span className="ml-auto shrink-0 rounded-full border border-[var(--border-faint)] bg-[var(--bg)] px-2 py-0.5 font-mono text-[10px] text-[var(--text-faint)]">
              {log.nodeId}
            </span>
          )}
        </div>
      }
      footer={
        <div className="flex shrink-0 items-center gap-1.5 border-t border-[var(--border-faint)] px-2.5 py-2">
          <button
            onClick={fixWithCopilot}
            disabled={!log.nodeId}
            className="inline-flex items-center gap-1.5 rounded-[8px] bg-[var(--accent)] px-2.5 py-1.5 text-[11.5px] font-semibold text-white transition-all hover:brightness-110 disabled:opacity-40"
          >
            <Bot className="h-3.5 w-3.5" /> Fix with Copilot
          </button>
          <button
            onClick={inspectNode}
            disabled={!log.nodeId}
            className="inline-flex items-center gap-1.5 rounded-[8px] border border-[var(--border-faint)] px-2.5 py-1.5 text-[11.5px] font-medium text-[var(--text-mute)] transition-colors hover:border-[var(--border)] hover:text-[var(--text)] disabled:opacity-40"
          >
            <SlidersHorizontal className="h-3.5 w-3.5" /> Inspect node
          </button>
          <button
            onClick={copyError}
            className="ml-auto inline-flex items-center gap-1.5 rounded-[8px] px-2.5 py-1.5 text-[11.5px] font-medium text-[var(--text-faint)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-[var(--ok)]" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      }
    />
  )
}

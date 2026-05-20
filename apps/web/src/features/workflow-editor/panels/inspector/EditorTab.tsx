import React, { useState, useEffect, useCallback } from 'react'
import { ChevronDown, Copy, Check, RefreshCw, Clock, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useWorkflowStore } from '@/stores/workflow-store'
import { useNodeAncestors } from '@/features/workflow-editor/hooks/use-node-ancestors'
import { useEditorLayout } from './hooks/use-editor-layout'
import { ConnectionsPanel } from './components/connections-panel'
import { InterpolationPicker } from './components/interpolation-picker'
import { PropertyGroupList } from './components/PropertyGroupList'
import type { CanonicalModeOverrides } from './visibility'
import apiClient from '@/lib/api/client'

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="flex-1 flex items-center justify-center p-8 text-center">
    <span className="text-[14px] text-text-muted font-medium leading-relaxed">{message}</span>
  </div>
)

const WebhookInfoBanner: React.FC<{
  path: string
  onGenerateSecret: () => void
  onPropertyChange: (name: string, value: any) => void
}> = ({ path, onGenerateSecret }) => {
  const [copied, setCopied] = useState(false)
  const apiBase = (import.meta.env.VITE_API_URL || '/api/v1').replace('/api/v1', '')
  const webhookUrl = path ? `${apiBase}/api/v1/webhooks/${path}` : null

  const copy = () => {
    if (!webhookUrl) return
    navigator.clipboard.writeText(webhookUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="mb-4 rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface-2)] p-3 flex flex-col gap-2">
      <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Webhook URL</span>
      {webhookUrl ? (
        <div className="flex items-center gap-2">
          <code className="flex-1 text-[11px] text-white bg-[var(--bg-surface-3)] rounded px-2 py-1.5 truncate font-mono">
            {webhookUrl}
          </code>
          <button
            onClick={copy}
            className="flex-shrink-0 p-1.5 rounded hover:bg-[var(--bg-surface-3)] text-[var(--text-muted)] hover:text-white transition-colors"
            title="Copy URL"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      ) : (
        <span className="text-[12px] text-[var(--text-muted)] italic">Set a webhook path above</span>
      )}
      <button
        onClick={onGenerateSecret}
        className="flex items-center gap-1.5 text-[11px] text-[var(--text-muted)] hover:text-white transition-colors w-fit"
      >
        <RefreshCw className="w-3 h-3" />
        Generate signing secret
      </button>
    </div>
  )
}

const CronInfoBanner: React.FC<{ expression: string }> = ({ expression }) => {
  const [nextRuns, setNextRuns] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const fetchNextRuns = useCallback(async (expr: string) => {
    if (!expr.trim()) { setNextRuns([]); setError(null); return }
    try {
      const res = await apiClient.get('/cron/next-runs', { params: { expression: expr, count: 3 } })
      setNextRuns(res.data.next_runs || [])
      setError(null)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Invalid expression')
      setNextRuns([])
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => fetchNextRuns(expression), 400)
    return () => clearTimeout(t)
  }, [expression, fetchNextRuns])

  const fmt = (iso: string) => new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })

  return (
    <div className="mb-4 rounded-lg border border-[var(--border-default)] bg-[var(--bg-surface-2)] p-3 flex flex-col gap-2">
      <div className="flex items-center gap-1.5">
        <Clock className="w-3.5 h-3.5 text-[var(--text-muted)]" />
        <span className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Next Runs</span>
      </div>
      {error ? (
        <div className="flex items-center gap-1.5 text-[12px] text-red-400">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          {error}
        </div>
      ) : nextRuns.length > 0 ? (
        <div className="flex flex-col gap-1">
          {nextRuns.map((r, i) => (
            <span key={i} className="text-[12px] text-white font-mono">{fmt(r)}</span>
          ))}
        </div>
      ) : (
        <span className="text-[12px] text-[var(--text-muted)] italic">Enter a cron expression above</span>
      )}
    </div>
  )
}

// ─── EditorTab ────────────────────────────────────────────────────────────────

export const EditorTab: React.FC = () => {
  const { nodes, edges, selectedNodeId, nodeSelectionTimestamp, updateNodeData, nodeDefinitions } = useWorkflowStore()
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [usedFields, setUsedFields] = useState<Set<string>>(new Set())
  const [picker, setPicker] = useState<{ rect: DOMRect; onSelect: (val: string) => void } | null>(null)

  useEffect(() => {
    setUsedFields(new Set())
    setPicker(null)
  }, [selectedNodeId, nodeSelectionTimestamp])

  const selectedNode = nodes.find(n => n.id === selectedNodeId)
  const definition = selectedNode ? nodeDefinitions.find(d => d.type === selectedNode.type) : null
  const properties: Record<string, any> = selectedNode?.data?.properties || {}
  const canonicalModes: CanonicalModeOverrides = selectedNode?.data?.canonicalModes || {}

  const connectedNodes = useNodeAncestors(selectedNodeId, nodes, edges)
  const { mainGroups, advancedProps, hasAdvanced, canonicalIndex } = useEditorLayout(
    definition,
    properties,
    canonicalModes,
  )

  if (!selectedNode) return <EmptyState message="Select a node on the canvas to configure its properties" />
  if (!definition) return <EmptyState message={`Metadata not available for: ${selectedNode.type}`} />

  const handlePropertyChange = (name: string, value: any) => {
    updateNodeData(selectedNode.id, {
      properties: { ...(selectedNode.data?.properties || {}), [name]: value },
    })
  }

  const toggleCanonicalMode = (canonicalId: string, currentMode: 'basic' | 'advanced') => {
    const next: 'basic' | 'advanced' = currentMode === 'basic' ? 'advanced' : 'basic'
    updateNodeData(selectedNode.id, {
      canonicalModes: { ...canonicalModes, [canonicalId]: next },
    })
  }

  const isEmpty = mainGroups.every(g => g.props.length === 0) && !hasAdvanced

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-[var(--bg)] relative">
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 pb-10">
        {selectedNode.type === 'trigger.cron' && (
          <CronInfoBanner expression={properties.cron_expression || ''} />
        )}

        {selectedNode.type === 'trigger.webhook' && (
          <WebhookInfoBanner
            path={properties.path || ''}
            onGenerateSecret={async () => {
              try {
                const res = await apiClient.post('/webhooks/utils/generate-secret')
                handlePropertyChange('secret', res.data.secret)
                handlePropertyChange('require_signature', true)
              } catch {}
            }}
            onPropertyChange={handlePropertyChange}
          />
        )}

        {isEmpty && (
          <p className="py-8 text-center text-[13px] text-[var(--text-muted)]">
            This node has no configurable properties.
          </p>
        )}

        <PropertyGroupList
          groups={mainGroups}
          selectedNode={selectedNode}
          definition={definition}
          properties={properties}
          canonicalIndex={canonicalIndex}
          canonicalModes={canonicalModes}
          onPropertyChange={handlePropertyChange}
          onShowPicker={(rect, onSelect) => setPicker({ rect, onSelect })}
          isFirstClickAllowed={(subId) => !usedFields.has(subId || '')}
          onFirstClickUsed={(subId) => setUsedFields(prev => new Set(prev).add(subId || ''))}
          onCanonicalToggle={toggleCanonicalMode}
        />

        {hasAdvanced && (
          <div className="mt-8 flex flex-col">
            <div
              onClick={() => setShowAdvanced(v => !v)}
              className="flex items-center justify-center gap-3 cursor-pointer group mb-2"
            >
              <div className="flex-1 h-[1px] border-b border-dashed border-border" />
              <span className="text-[12px] font-bold text-white flex items-center gap-1.5 hover:text-[var(--text-muted)] transition-colors">
                Show additional fields
                <ChevronDown className={cn("w-3.5 h-3.5 transition-transform duration-200", showAdvanced && "rotate-180")} />
              </span>
              <div className="flex-1 h-[1px] border-b border-dashed border-border" />
            </div>

            {showAdvanced && (
              <div className="flex flex-col mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                <PropertyGroupList
                  groups={[{ group: null, props: advancedProps }]}
                  selectedNode={selectedNode}
                  definition={definition}
                  properties={properties}
                  canonicalIndex={canonicalIndex}
                  canonicalModes={canonicalModes}
                  onPropertyChange={handlePropertyChange}
                  onShowPicker={(rect, onSelect) => setPicker({ rect, onSelect })}
                  isFirstClickAllowed={(subId) => !usedFields.has(subId || '')}
                  onFirstClickUsed={(subId) => setUsedFields(prev => new Set(prev).add(subId || ''))}
                  onCanonicalToggle={toggleCanonicalMode}
                />
              </div>
            )}
          </div>
        )}
      </div>

      <ConnectionsPanel connectedNodes={connectedNodes} />

      {picker && (
        <InterpolationPicker
          anchorRect={picker.rect}
          onSelect={(val) => { picker.onSelect(val); setPicker(null) }}
          onClose={() => setPicker(null)}
        />
      )}
    </div>
  )
}

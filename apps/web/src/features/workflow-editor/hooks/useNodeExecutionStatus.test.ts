import { beforeEach, describe, expect, it } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useNodeExecutionStatus } from './useNodeExecutionStatus'
import { useListenState } from './useHostedListen'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useRunsStore, type Run, type RunStatus, type NodeRunStatus } from '@/features/runs/store/runsStore'
import type { WorkflowDetail } from '../types/editorTypes'

const WF_ID = 'wf-1'
const TRIGGER = 'trigger-1'
const AGENT = 'agent-1'

const workflow: WorkflowDetail = {
  id: WF_ID,
  name: 'test',
  is_active: true,
  kind: 'automation',
  graph: {},
  version_vector: 0,
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-01T00:00:00Z',
}

function setLatestRun(status: RunStatus, nodeStatuses: Record<string, NodeRunStatus>) {
  const run: Run = { executionId: 'exec-1', status, logs: [], nodeStatuses }
  useRunsStore.setState({
    byWorkflow: {
      [WF_ID]: { runs: [run], activeExecutionId: run.executionId, selectedLogId: null },
    },
  })
}

function status(nodeId: string) {
  return renderHook(() => useNodeExecutionStatus(nodeId)).result.current
}

describe('useNodeExecutionStatus — listen pulse vs real run status precedence', () => {
  beforeEach(() => {
    useWorkflowEditorStore.setState({ workflow })
    useRunsStore.setState({ byWorkflow: {} })
    useListenState.getState().set(null)
  })

  it('run in flight: real per-node statuses win over the listening pulse', () => {
    useListenState.getState().set(WF_ID, TRIGGER)
    setLatestRun('running', { [TRIGGER]: 'completed', [AGENT]: 'running' })

    // The trigger already completed inside this run — the pulse must not
    // mask that while the execution is flowing.
    expect(status(TRIGGER)).toBe('completed')
    expect(status(AGENT)).toBe('running')
  })

  it('idle + listening: the trigger node pulses as running', () => {
    useListenState.getState().set(WF_ID, TRIGGER)
    // No runs at all — the graph is live, waiting on the visitor.

    expect(status(TRIGGER)).toBe('running')
    // Only the listening trigger pulses; other nodes stay idle.
    expect(status(AGENT)).toBeNull()
  })

  it('terminal run + still listening: the pulse resumes on the trigger', () => {
    useListenState.getState().set(WF_ID, TRIGGER)
    setLatestRun('completed', { [TRIGGER]: 'completed', [AGENT]: 'completed' })

    expect(status(TRIGGER)).toBe('running')
    // Downstream nodes keep their terminal marks between submissions.
    expect(status(AGENT)).toBe('completed')
  })

  it('failed node marks survive — not overwritten by the listening pulse', () => {
    useListenState.getState().set(WF_ID, TRIGGER)
    setLatestRun('failed', { [TRIGGER]: 'completed', [AGENT]: 'failed' })

    expect(status(AGENT)).toBe('failed')
  })

  it('not listening + no runs: null', () => {
    expect(status(TRIGGER)).toBeNull()
  })

  it('listen state for another workflow does not pulse this editor', () => {
    useListenState.getState().set('wf-other', TRIGGER)

    expect(status(TRIGGER)).toBeNull()
  })

  it('falls back to log scanning when no explicit node status was recorded', () => {
    const run: Run = {
      executionId: 'exec-legacy',
      status: 'failed',
      nodeStatuses: {},
      logs: [
        {
          id: 'log-1',
          nodeId: AGENT,
          level: 'error',
          message: 'boom',
          payload: { error: 'boom' },
          timestamp: '2026-07-01T00:00:01Z',
        },
      ],
    }
    useRunsStore.setState({
      byWorkflow: {
        [WF_ID]: { runs: [run], activeExecutionId: run.executionId, selectedLogId: null },
      },
    })

    expect(status(AGENT)).toBe('failed')
    expect(status(TRIGGER)).toBeNull()
  })
})

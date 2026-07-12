import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, renderHook } from '@testing-library/react'
import { useHostedListen, useListenState } from './useHostedListen'
import { useRunsStore } from '@/features/runs/store/runsStore'

// The message handler reads startRun / setActiveExecutionId off the runs
// store at dispatch time (getState()), so swapping them for spies via
// setState is exactly how the hook consumes them.
const realActions = {
  startRun: useRunsStore.getState().startRun,
  setActiveExecutionId: useRunsStore.getState().setActiveExecutionId,
}
const startRun = vi.fn()
const setActiveExecutionId = vi.fn()

// Module-level dedup (`lastSeenExecutionId`) can't be reset from tests, so
// every test uses a unique execution id.
function postExecution(executionId: string, origin = window.location.origin) {
  act(() => {
    window.dispatchEvent(
      new MessageEvent('message', {
        origin,
        data: { type: 'fuse-app-execution', executionId },
      }),
    )
  })
}

function enableListen(workflowId: string, nodeId: string | null = null) {
  act(() => {
    useListenState.getState().set(workflowId, nodeId)
  })
}

describe('useHostedListen — hosted-app execution messages', () => {
  beforeEach(() => {
    startRun.mockClear()
    setActiveExecutionId.mockClear()
    useRunsStore.setState({ startRun, setActiveExecutionId, byWorkflow: {} })
    useListenState.getState().set(null)
  })

  afterEach(() => {
    cleanup()
    useRunsStore.setState(realActions)
  })

  it('starts the run AND sets the active execution id on a valid message', () => {
    renderHook(() => useHostedListen('wf-a'))
    enableListen('wf-a')

    postExecution('exec-1')

    // Both are required: startRun alone appends the row but the execution
    // websocket keys off activeExecutionId — the 2026-07-11 bug class.
    expect(startRun).toHaveBeenCalledTimes(1)
    expect(startRun).toHaveBeenCalledWith('wf-a', 'exec-1')
    expect(setActiveExecutionId).toHaveBeenCalledTimes(1)
    expect(setActiveExecutionId).toHaveBeenCalledWith('wf-a', 'exec-1')
  })

  it('ignores messages from a foreign origin', () => {
    renderHook(() => useHostedListen('wf-a'))
    enableListen('wf-a')

    postExecution('exec-2', 'https://evil.example.com')

    expect(startRun).not.toHaveBeenCalled()
    expect(setActiveExecutionId).not.toHaveBeenCalled()
  })

  it('ignores messages that are not fuse-app-execution or lack an id', () => {
    renderHook(() => useHostedListen('wf-a'))
    enableListen('wf-a')

    act(() => {
      window.dispatchEvent(
        new MessageEvent('message', {
          origin: window.location.origin,
          data: { type: 'something-else', executionId: 'exec-x' },
        }),
      )
      window.dispatchEvent(
        new MessageEvent('message', {
          origin: window.location.origin,
          data: { type: 'fuse-app-execution' },
        }),
      )
    })

    expect(startRun).not.toHaveBeenCalled()
  })

  it('processes the same execution id once across duplicate deliveries and hook instances', () => {
    // Action bar + editor page both mount the hook → two listeners.
    renderHook(() => useHostedListen('wf-a'))
    renderHook(() => useHostedListen('wf-a'))
    enableListen('wf-a')

    postExecution('exec-3')
    postExecution('exec-3')

    expect(startRun).toHaveBeenCalledTimes(1)
    expect(setActiveExecutionId).toHaveBeenCalledTimes(1)
  })

  it('keys listen state by workflow id — workflow A does not leak into workflow B', () => {
    const a = renderHook(() => useHostedListen('wf-a'))
    const b = renderHook(() => useHostedListen('wf-b'))

    enableListen('wf-a')

    expect(a.result.current.listening).toBe(true)
    expect(b.result.current.listening).toBe(false)

    // Only the listening workflow's instance handles the message.
    postExecution('exec-4')
    expect(startRun).toHaveBeenCalledTimes(1)
    expect(startRun).toHaveBeenCalledWith('wf-a', 'exec-4')

    // stopListening from the active instance clears the shared flag.
    act(() => a.result.current.stopListening())
    expect(a.result.current.listening).toBe(false)
    expect(useListenState.getState().activeFor).toBeNull()
  })
})

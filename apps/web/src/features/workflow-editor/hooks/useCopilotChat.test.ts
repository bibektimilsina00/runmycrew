/**
 * Copilot is workflow-only (its backend routes are WorkflowRepository-
 * scoped). On a crew editor the id is a crew id, so every copilot call
 * 404s — the hook must not fire them there.
 */
import { renderHook, act } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { copilotAPI } from '../services/copilotAPI'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useCopilotChat } from './useCopilotChat'

vi.mock('../services/copilotAPI', async () => {
  const actual = await vi.importActual<typeof import('../services/copilotAPI')>(
    '../services/copilotAPI',
  )
  return {
    ...actual,
    copilotAPI: {
      listSessions: vi.fn().mockResolvedValue([]),
      getSession: vi.fn().mockResolvedValue({ messages: [] }),
      deleteSession: vi.fn().mockResolvedValue(undefined),
    },
  }
})

function setEditor(mode: 'workflow' | 'crew') {
  useWorkflowEditorStore.setState({
    mode,
    workflow: { id: 'id-123', name: 'x', graph: { nodes: [], edges: [] } } as never,
    nodes: [],
    selectedNodeId: null,
  })
}

afterEach(() => {
  vi.clearAllMocks()
  useWorkflowEditorStore.setState({ mode: 'workflow' })
})

describe('useCopilotChat crew gating', () => {
  it('loads sessions for a workflow', () => {
    setEditor('workflow')
    renderHook(() => useCopilotChat())
    expect(copilotAPI.listSessions).toHaveBeenCalledWith('id-123')
  })

  it('does NOT call copilot session endpoints for a crew', () => {
    setEditor('crew')
    renderHook(() => useCopilotChat())
    expect(copilotAPI.listSessions).not.toHaveBeenCalled()
  })

  it('send() on a crew sets an error instead of hitting the 404 path', async () => {
    setEditor('crew')
    const { result } = renderHook(() => useCopilotChat())
    await act(async () => {
      await result.current.send('hi')
    })
    expect(result.current.error).toMatch(/workflows, not crews/i)
  })
})

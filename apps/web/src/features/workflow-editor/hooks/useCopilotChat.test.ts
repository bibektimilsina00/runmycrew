/**
 * Copilot works for both workflows and crews — the backend resolves the id
 * as either kind and builds the graph with the same tools.
 */
import { renderHook } from '@testing-library/react'
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

describe('useCopilotChat works for workflows AND crews', () => {
  it('loads sessions for a workflow', () => {
    setEditor('workflow')
    renderHook(() => useCopilotChat())
    expect(copilotAPI.listSessions).toHaveBeenCalledWith('id-123')
  })

  it('loads sessions for a crew too (backend resolves either kind)', () => {
    setEditor('crew')
    renderHook(() => useCopilotChat())
    expect(copilotAPI.listSessions).toHaveBeenCalledWith('id-123')
  })
})

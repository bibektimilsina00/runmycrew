import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import type { Node, Edge } from 'reactflow'
import { HelpCircle, Code2, Search, Wrench, Sparkles } from 'lucide-react'
import { streamCopilotChat, copilotAPI, type SessionItem } from '../services/copilotAPI'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'
import { useCopilotDiffStore, type StreamingOp } from '../stores/copilotDiffStore'
import { useCopilotPendingStore } from '../stores/copilotPendingStore'

export type ToolCallStatus = 'running' | 'success' | 'failed'

export interface ToolCall {
  tool: string
  status: ToolCallStatus
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  toolCalls?: ToolCall[]
}

export interface SlashCommand {
  cmd: string
  hint: string
  Icon: React.FC<{ className?: string }>
}

export const SLASH_COMMANDS: SlashCommand[] = [
  { cmd: '/fix', hint: 'Fix the selected node', Icon: Wrench },
  { cmd: '/explain', hint: 'Explain what this node does', Icon: HelpCircle },
  { cmd: '/improve', hint: 'Suggest an improvement', Icon: Sparkles },
  { cmd: '/test', hint: 'Generate a test payload', Icon: Code2 },
  { cmd: '/find', hint: 'Find a node or integration', Icon: Search },
]

const INITIAL_MESSAGES: ChatMessage[] = []

export function useCopilotChat() {
  const [msgs, setMsgs] = useState<ChatMessage[]>(INITIAL_MESSAGES)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [slashOpen, setSlashOpen] = useState(false)
  const [slashIdx, setSlashIdx] = useState(0)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessions, setSessions] = useState<SessionItem[]>([])
  const streamRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  const nodes = useWorkflowEditorStore(s => s.nodes)
  const selectedNodeId = useWorkflowEditorStore(s => s.selectedNodeId)
  const selectedNode = nodes.find(n => n.id === selectedNodeId)
  const workflowId = useWorkflowEditorStore(s => s.workflow?.id)

  // Load sessions when the workflow opens.
  useEffect(() => {
    if (!workflowId) return
    let cancelled = false
    void copilotAPI
      .listSessions(workflowId)
      .then(s => {
        if (!cancelled) setSessions(s)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [workflowId])

  const refreshSessions = () => {
    if (workflowId) void copilotAPI.listSessions(workflowId).then(setSessions).catch(() => {})
  }

  const newChat = () => {
    setMsgs(INITIAL_MESSAGES)
    setSessionId(null)
    useCopilotDiffStore.getState().reject()
  }

  const loadSession = async (id: string) => {
    if (!workflowId) return
    try {
      const s = await copilotAPI.getSession(workflowId, id)
      setMsgs(s.messages as ChatMessage[])
      setSessionId(id)
    } catch {
      setError('Could not load session.')
    }
  }

  const deleteSession = async (id: string) => {
    if (!workflowId) return
    await copilotAPI.deleteSession(workflowId, id).catch(() => {})
    if (id === sessionId) newChat()
    refreshSessions()
  }

  const slashFilter =
    input.startsWith('/') && !input.includes(' ')
      ? SLASH_COMMANDS.filter(c => c.cmd.startsWith(input))
      : []

  const updateInput = (next: string) => {
    setInput(next)
    const filtered =
      next.startsWith('/') && !next.includes(' ')
        ? SLASH_COMMANDS.filter(c => c.cmd.startsWith(next))
        : []
    setSlashOpen(filtered.length > 0)
    setSlashIdx(0)
  }

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight
    })
  }

  const appendToAssistant = (text: string) => {
    setMsgs(m => {
      const copy = [...m]
      const last = copy[copy.length - 1]
      if (last?.role === 'assistant') copy[copy.length - 1] = { ...last, content: last.content + text }
      return copy
    })
    scrollToBottom()
  }

  const appendToolCall = (tool: string) => {
    setMsgs(m => {
      const copy = [...m]
      const last = copy[copy.length - 1]
      if (last?.role !== 'assistant') return copy
      copy[copy.length - 1] = {
        ...last,
        toolCalls: [...(last.toolCalls ?? []), { tool, status: 'running' }],
      }
      return copy
    })
  }

  const finalizeToolCall = (tool: string, status: 'success' | 'failed') => {
    setMsgs(m => {
      const copy = [...m]
      const last = copy[copy.length - 1]
      if (last?.role !== 'assistant' || !last.toolCalls?.length) return copy
      const calls = [...last.toolCalls]
      for (let i = calls.length - 1; i >= 0; i--) {
        if (calls[i].status === 'running' && (calls[i].tool === tool || !tool)) {
          calls[i] = { ...calls[i], status }
          break
        }
      }
      copy[copy.length - 1] = { ...last, toolCalls: calls }
      return copy
    })
  }

  const send = async (text?: string, baseMsgs?: ChatMessage[]) => {
    const content = (text ?? input).trim()
    if (!content || busy) return

    const editor = useWorkflowEditorStore.getState()
    const workflowId = editor.workflow?.id
    if (!workflowId) {
      setError('Open a workflow to use Copilot.')
      return
    }

    const seed = baseMsgs ?? msgs
    const userMsg: ChatMessage = { role: 'user', content }
    const history = [...seed, userMsg]
      .filter(m => m.content)
      .map(m => ({ role: m.role, content: m.content }))

    setMsgs(() => [...seed, userMsg, { role: 'assistant', content: '' }])
    updateInput('')
    setBusy(true)
    setError(null)
    scrollToBottom()

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const stream = streamCopilotChat(
        workflowId,
        {
          messages: history,
          graph: { nodes: editor.nodes, edges: editor.edges },
          session_id: sessionId,
        },
        controller.signal,
      )
      for await (const ev of stream) {
        if (ev.type === 'text_delta') {
          appendToAssistant(String(ev.content ?? ''))
        } else if (ev.type === 'tool_start') {
          const tool = String(ev.tool ?? 'tool')
          appendToolCall(tool)
          // First graph-mutating tool of the turn → open an empty diff so the
          // canvas can paint subsequent graph_op events as they arrive.
          if (
            tool === 'add_node' ||
            tool === 'update_node' ||
            tool === 'remove_node' ||
            tool === 'add_edge' ||
            tool === 'remove_edge' ||
            tool === 'set_workflow_name'
          ) {
            useCopilotDiffStore.getState().startStreaming()
          }
        } else if (ev.type === 'tool_result') {
          finalizeToolCall(String(ev.tool ?? ''), ev.success === false ? 'failed' : 'success')
        } else if (ev.type === 'graph_op') {
          // Atomic op from the engine — apply to the in-progress proposed graph
          // so the user sees each node/edge appear one at a time.
          useCopilotDiffStore.getState().applyOp(ev as unknown as StreamingOp)
        } else if (ev.type === 'workflow_proposed') {
          // Final canonical resolve. Reconciles any drift between the streamed
          // ops and the server's authoritative graph.
          useCopilotDiffStore.getState().setProposal(
            ev.graph as { nodes: Node[]; edges: Edge[] },
            typeof ev.name === 'string' ? ev.name : null,
          )
        } else if (ev.type === 'session_saved') {
          setSessionId(String(ev.session_id ?? '') || null)
        } else if (ev.type === 'error') {
          setError(String(ev.message ?? 'Copilot error'))
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError') setError((e as Error).message)
    } finally {
      setBusy(false)
      abortRef.current = null
      // If the model only ran tools and produced no prose, leave a confirmation.
      setMsgs(m => {
        const copy = [...m]
        const last = copy[copy.length - 1]
        if (last?.role === 'assistant' && !last.content) {
          copy[copy.length - 1] = { ...last, content: 'Done.' }
        }
        return copy
      })
      refreshSessions()
    }
  }

  const cancel = () => {
    abortRef.current?.abort()
    setBusy(false)
  }

  /** Re-run the user prompt that produced the given assistant message. */
  const retryFromAssistant = (assistantIdx: number) => {
    let userIdx = -1
    for (let i = assistantIdx - 1; i >= 0; i--) {
      if (msgs[i].role === 'user') { userIdx = i; break }
    }
    if (userIdx < 0) return
    const userText = msgs[userIdx].content
    const truncated = msgs.slice(0, userIdx)
    setMsgs(truncated)
    void send(userText, truncated)
  }

  /** Replace a user message's content and re-run from that point. */
  const editAndResend = (userIdx: number, newContent: string) => {
    if (msgs[userIdx]?.role !== 'user') return
    const truncated = msgs.slice(0, userIdx)
    setMsgs(truncated)
    void send(newContent, truncated)
  }

  // "Fix with Copilot" and other surfaces dispatch a prefilled message.
  const sendRef = useRef(send)
  useEffect(() => {
    sendRef.current = send
  })
  useEffect(() => {
    const handler = (e: Event) => {
      const message = (e as CustomEvent<{ message?: string }>).detail?.message
      if (message) void sendRef.current(message)
    }
    window.addEventListener('copilot-send-message', handler)
    return () => window.removeEventListener('copilot-send-message', handler)
  }, [])

  // Pending-prompt handoff (e.g. dashboard → editor): consume once on mount.
  const seedConsumedRef = useRef(false)
  useEffect(() => {
    if (!workflowId || seedConsumedRef.current) return
    const seed = useCopilotPendingStore.getState().consume()
    if (seed) {
      seedConsumedRef.current = true
      void sendRef.current(seed)
    }
  }, [workflowId])

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (slashOpen) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSlashIdx(i => Math.min(slashFilter.length - 1, i + 1))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSlashIdx(i => Math.max(0, i - 1))
        return
      }
      if (e.key === 'Tab' || (e.key === 'Enter' && slashFilter[slashIdx])) {
        e.preventDefault()
        updateInput(slashFilter[slashIdx].cmd + ' ')
        return
      }
      if (e.key === 'Escape') {
        e.preventDefault()
        setSlashOpen(false)
        return
      }
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send()
    }
  }

  const selectSlashCommand = (cmd: string) => {
    updateInput(cmd + ' ')
    inputRef.current?.focus()
  }

  const label = (selectedNode?.data?.label as string) || selectedNode?.type || 'this node'
  const quickActions = selectedNode
    ? [
        { label: 'Explain node', text: `/explain ${label}` },
        { label: 'Improve', text: `/improve ${label}` },
        { label: 'Fix', text: `/fix ${label}` },
      ]
    : [
        { label: 'Build a workflow', text: 'Build a workflow that ' },
        { label: 'Add a step', text: 'Add a step that ' },
        { label: 'Explain flow', text: '/explain the workflow' },
      ]

  return {
    msgs,
    input,
    setInput: updateInput,
    busy,
    error,
    slashOpen,
    slashIdx,
    setSlashIdx,
    slashFilter,
    streamRef,
    inputRef,
    quickActions,
    send,
    cancel,
    retryFromAssistant,
    editAndResend,
    onKeyDown,
    selectSlashCommand,
    // sessions
    sessions,
    sessionId,
    newChat,
    loadSession,
    deleteSession,
  }
}

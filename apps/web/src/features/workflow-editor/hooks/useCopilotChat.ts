import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { HelpCircle, Code2, Search, Wrench } from 'lucide-react'
import { Sparkles } from 'lucide-react'
import { useWorkflowEditorStore } from '../stores/workflowEditorStore'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface SlashCommand {
  cmd: string
  hint: string
  Icon: React.FC<{ className?: string }>
}

export const SLASH_COMMANDS: SlashCommand[] = [
  { cmd: '/fix',     hint: 'Suggest a fix for the selected node',      Icon: Wrench },
  { cmd: '/explain', hint: 'Explain what this node does',              Icon: HelpCircle },
  { cmd: '/improve', hint: 'Suggest an improvement to this workflow',  Icon: Sparkles },
  { cmd: '/test',    hint: 'Generate a test payload for this trigger', Icon: Code2 },
  { cmd: '/find',    hint: 'Find a tool or app to connect',            Icon: Search },
]

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    role: 'assistant',
    content: "Hi — I can fix node errors, explain steps, generate test payloads, or suggest tools. Try a slash command, or just ask.",
  },
]

export function useCopilotChat() {
  const [msgs, setMsgs]           = useState<ChatMessage[]>(INITIAL_MESSAGES)
  const [input, setInput]         = useState('')
  const [busy, setBusy]           = useState(false)
  const [slashOpen, setSlashOpen] = useState(false)
  const [slashIdx, setSlashIdx]   = useState(0)
  const streamRef                 = useRef<HTMLDivElement>(null)
  const inputRef                  = useRef<HTMLTextAreaElement>(null)

  const nodes          = useWorkflowEditorStore(s => s.nodes)
  const selectedNodeId = useWorkflowEditorStore(s => s.selectedNodeId)
  const selectedNode   = nodes.find(n => n.id === selectedNodeId)

  const slashFilter = input.startsWith('/') && !input.includes(' ')
    ? SLASH_COMMANDS.filter(c => c.cmd.startsWith(input))
    : []

  // Update input and keep the slash menu in sync — derived from the new value,
  // so it lives in the change handler rather than an effect.
  const updateInput = (next: string) => {
    setInput(next)
    const filtered = next.startsWith('/') && !next.includes(' ')
      ? SLASH_COMMANDS.filter(c => c.cmd.startsWith(next))
      : []
    setSlashOpen(filtered.length > 0)
    setSlashIdx(0)
  }

  // Auto-scroll to latest message
  useEffect(() => {
    if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight
  }, [msgs, busy])

  const send = async (text?: string) => {
    const t = (text ?? input).trim()
    if (!t || busy) return
    setMsgs(m => [...m, { role: 'user', content: t }])
    updateInput('')
    setBusy(true)
    try {
      // TODO: replace with real Copilot API call
      await new Promise(r => setTimeout(r, 900))
      const nodeCtx = selectedNode
        ? `for node "${selectedNode.data?.label ?? selectedNode.type}"`
        : ''
      setMsgs(m => [...m, {
        role: 'assistant',
        content: `I understand — you're asking ${nodeCtx}: "${t}". Connect the Copilot API to get real answers here.`,
      }])
    } finally {
      setBusy(false)
    }
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (slashOpen) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setSlashIdx(i => Math.min(slashFilter.length - 1, i + 1)); return }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setSlashIdx(i => Math.max(0, i - 1)); return }
      if (e.key === 'Tab' || (e.key === 'Enter' && slashFilter[slashIdx])) {
        e.preventDefault()
        updateInput(slashFilter[slashIdx].cmd + ' ')
        return
      }
      if (e.key === 'Escape') { e.preventDefault(); setSlashOpen(false); return }
    }
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send() }
  }

  const selectSlashCommand = (cmd: string) => {
    updateInput(cmd + ' ')
    inputRef.current?.focus()
  }

  const quickActions = selectedNode
    ? [
        { label: 'Explain node',  text: `/explain ${selectedNode.data?.label ?? selectedNode.type}` },
        { label: 'Generate test', text: `/test ${selectedNode.data?.label ?? selectedNode.type}` },
        { label: 'Suggest fix',   text: `/fix ${selectedNode.data?.label ?? selectedNode.type}` },
      ]
    : [
        { label: 'Improve workflow', text: '/improve the workflow' },
        { label: 'Find a tool',      text: '/find' },
        { label: 'Explain flow',     text: '/explain the workflow' },
      ]

  return {
    msgs,
    input,
    setInput: updateInput,
    busy,
    slashOpen,
    slashIdx,
    setSlashIdx,
    slashFilter,
    streamRef,
    inputRef,
    quickActions,
    send,
    onKeyDown,
    selectSlashCommand,
  }
}

import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ChevronsUpDown, ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import {
  hasInterpolationDragData,
  insertInterpolationAtSelection,
  readInterpolationDragData,
} from '@/features/workflow-editor/utils/interpolation'

type MessageRole = 'system' | 'user' | 'assistant'

interface AgentMessage {
  role: MessageRole
  content: string
}

interface MessagesInputProps {
  value: unknown
  onChange: (val: AgentMessage[]) => void
}

const MESSAGE_ROLES: MessageRole[] = ['user', 'system', 'assistant']
const MIN_TEXTAREA_HEIGHT = 84
const DEFAULT_MESSAGES: AgentMessage[] = [{ role: 'user', content: '' }]

function isMessageRole(value: string): value is MessageRole {
  return MESSAGE_ROLES.some((role) => role === value)
}

function formatRole(role: MessageRole): string {
  return role.charAt(0).toUpperCase() + role.slice(1)
}

function normalizeMessages(value: unknown): AgentMessage[] {
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return DEFAULT_MESSAGES

    try {
      return normalizeMessages(JSON.parse(trimmed))
    } catch {
      return [{ role: 'user', content: value }]
    }
  }

  if (!Array.isArray(value)) return DEFAULT_MESSAGES

  const messages = value
    .filter((message): message is Record<string, unknown> => (
      typeof message === 'object' && message !== null
    ))
    .map((message) => {
      const role = typeof message.role === 'string' && isMessageRole(message.role)
        ? message.role
        : 'user'

      return {
        role,
        content: typeof message.content === 'string' ? message.content : '',
      }
    })

  return messages.length > 0 ? messages : DEFAULT_MESSAGES
}

function resizeTextarea(textarea: HTMLTextAreaElement): void {
  textarea.style.height = 'auto'
  textarea.style.height = `${Math.max(MIN_TEXTAREA_HEIGHT, textarea.scrollHeight)}px`
}

export const MessagesInput: React.FC<MessagesInputProps> = ({ value, onChange }) => {
  const [messages, setMessages] = useState<AgentMessage[]>(() => normalizeMessages(value))
  const [openRoleIndex, setOpenRoleIndex] = useState<number | null>(null)
  const textareaRefs = useRef<Record<string, HTMLTextAreaElement | null>>({})
  const resizeStateRef = useRef<{
    fieldId: string
    startY: number
    startHeight: number
  } | null>(null)

  const normalizedValue = useMemo(() => normalizeMessages(value), [value])

  useEffect(() => {
    setMessages(normalizedValue)
  }, [normalizedValue])

  useEffect(() => {
    messages.forEach((_, index) => {
      const textarea = textareaRefs.current[`message-${index}`]
      if (textarea) resizeTextarea(textarea)
    })
  }, [messages])

  const commitMessages = (nextMessages: AgentMessage[]) => {
    setMessages(nextMessages)
    onChange(nextMessages)
  }

  const updateMessage = (index: number, patch: Partial<AgentMessage>) => {
    commitMessages(messages.map((message, messageIndex) => (
      messageIndex === index ? { ...message, ...patch } : message
    )))
  }

  const addMessageAfter = (index: number) => {
    const nextMessages = [...messages]
    nextMessages.splice(index + 1, 0, { role: 'user', content: '' })
    commitMessages(nextMessages)
  }

  const deleteMessage = (index: number) => {
    if (messages.length === 1) return
    commitMessages(messages.filter((_, messageIndex) => messageIndex !== index))
  }

  const moveMessage = (index: number, direction: -1 | 1) => {
    const targetIndex = index + direction
    if (targetIndex < 0 || targetIndex >= messages.length) return

    const nextMessages = [...messages]
    const current = nextMessages[index]
    nextMessages[index] = nextMessages[targetIndex]
    nextMessages[targetIndex] = current
    commitMessages(nextMessages)
  }

  const handleDragOver = (event: React.DragEvent<HTMLTextAreaElement>) => {
    if (!hasInterpolationDragData(event)) return
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
  }

  const handleDrop = (event: React.DragEvent<HTMLTextAreaElement>, index: number) => {
    const interpolation = readInterpolationDragData(event)
    if (!interpolation) return

    event.preventDefault()
    const target = event.currentTarget
    updateMessage(index, {
      content: insertInterpolationAtSelection(
        target.value,
        interpolation,
        target.selectionStart ?? target.value.length,
        target.selectionEnd ?? target.value.length,
      ),
    })
  }

  const startResize = (
    event: React.MouseEvent<HTMLDivElement>,
    fieldId: string,
  ) => {
    event.preventDefault()
    event.stopPropagation()

    const textarea = textareaRefs.current[fieldId]
    if (!textarea) return

    resizeStateRef.current = {
      fieldId,
      startY: event.clientY,
      startHeight: textarea.offsetHeight || MIN_TEXTAREA_HEIGHT,
    }

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const resizeState = resizeStateRef.current
      if (!resizeState) return

      const activeTextarea = textareaRefs.current[resizeState.fieldId]
      if (!activeTextarea) return

      const nextHeight = Math.max(
        MIN_TEXTAREA_HEIGHT,
        resizeState.startHeight + moveEvent.clientY - resizeState.startY,
      )
      activeTextarea.style.height = `${nextHeight}px`
    }

    const handleMouseUp = () => {
      resizeStateRef.current = null
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  return (
    <div className="flex w-full flex-col gap-2.5">
      {messages.map((message, index) => {
        const fieldId = `message-${index}`
        const isRoleOpen = openRoleIndex === index

        return (
          <div
            key={fieldId}
            className="relative flex w-full flex-col rounded-md border border-border bg-surface-editor"
          >
            <div className="flex items-center justify-between px-2 pt-1.5">
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setOpenRoleIndex(isRoleOpen ? null : index)}
                  className="flex h-6 items-center gap-1 rounded px-1.5 text-[12px] font-semibold text-white transition-colors hover:bg-surface-5"
                  aria-label="Select message role"
                >
                  {formatRole(message.role)}
                  <ChevronDown className={cn("size-3 transition-transform", isRoleOpen && "rotate-180")} />
                </button>
                {isRoleOpen && (
                  <div className="absolute left-0 top-7 z-50 min-w-[120px] rounded-md border border-border bg-surface-modal p-1 shadow-xl">
                    {MESSAGE_ROLES.map((role) => (
                      <button
                        key={role}
                        type="button"
                        onClick={() => {
                          updateMessage(index, { role })
                          setOpenRoleIndex(null)
                        }}
                        className={cn(
                          "flex h-7 w-full items-center rounded px-2 text-left text-[12px] text-text-muted transition-colors hover:bg-surface-5 hover:text-white",
                          message.role === role && "bg-surface-5 text-white",
                        )}
                      >
                        {formatRole(role)}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-0.5">
                {messages.length > 1 && (
                  <>
                    <Button
                      type="button"
                      variant="ghost"
                      size="xs"
                      className="size-6 p-0"
                      onClick={() => deleteMessage(index)}
                      aria-label="Delete message"
                    >
                      <Trash2 className="size-3.5" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="xs"
                      className="size-6 p-0"
                      disabled={index === 0}
                      onClick={() => moveMessage(index, -1)}
                      aria-label="Move message up"
                    >
                      <ChevronUp className="size-3.5" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="xs"
                      className="size-6 p-0"
                      disabled={index === messages.length - 1}
                      onClick={() => moveMessage(index, 1)}
                      aria-label="Move message down"
                    >
                      <ChevronDown className="size-3.5" />
                    </Button>
                  </>
                )}
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  className="size-6 p-0"
                  onClick={() => addMessageAfter(index)}
                  aria-label="Add message below"
                >
                  <Plus className="size-3.5" />
                </Button>
              </div>
            </div>

            <div className="relative">
              <textarea
                ref={(element) => {
                  textareaRefs.current[fieldId] = element
                }}
                value={message.content}
                onChange={(event) => {
                  updateMessage(index, { content: event.target.value })
                  resizeTextarea(event.target)
                }}
                onDragOver={handleDragOver}
                onDrop={(event) => handleDrop(event, index)}
                placeholder="Enter message content..."
                className="min-h-[84px] w-full resize-none overflow-y-auto bg-transparent px-2 pb-7 pt-2 text-[13px] leading-5 text-white outline-none placeholder:text-text-placeholder"
              />
              <div
                className="absolute bottom-1 right-1 flex size-5 cursor-ns-resize items-center justify-center rounded border border-border bg-surface-modal text-text-muted hover:text-white"
                onMouseDown={(event) => startResize(event, fieldId)}
                onDragStart={(event) => event.preventDefault()}
                title="Resize message"
              >
                <ChevronsUpDown className="size-3" />
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

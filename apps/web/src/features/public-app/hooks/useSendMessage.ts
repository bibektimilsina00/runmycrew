import { useCallback, useEffect, useRef, useState } from 'react'
import { publicAppAPI } from '../services/publicAppAPI'
import type { AppMessage } from '../types/publicAppTypes'

interface StreamState {
  status: 'idle' | 'sending' | 'streaming' | 'done' | 'error'
  assistant: AppMessage | null
  error: string | null
}

const EMPTY: StreamState = { status: 'idle', assistant: null, error: null }

/**
 * Owns one turn of the chat: POST the message → open SSE → merge deltas
 * into an in-flight assistant message → hand the final message to the
 * caller via `onComplete` so it can be appended to the transcript.
 *
 * Reconnect is handled by EventSource natively; we abort on unmount or
 * cancel.
 */
export function useSendMessage(
  workspaceSlug: string,
  appSlug: string,
  onComplete: (msg: AppMessage) => void,
) {
  const [state, setState] = useState<StreamState>(EMPTY)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    return () => {
      esRef.current?.close()
      esRef.current = null
    }
  }, [])

  const send = useCallback(
    async (message: string, formData?: Record<string, unknown>) => {
      esRef.current?.close()
      setState({ status: 'sending', assistant: null, error: null })

      let stream: Awaited<ReturnType<typeof publicAppAPI.sendMessage>>
      try {
        stream = await publicAppAPI.sendMessage(workspaceSlug, appSlug, {
          message,
          form_data: formData,
        })
      } catch (e) {
        setState({
          status: 'error',
          assistant: null,
          error: e instanceof Error ? e.message : 'Send failed',
        })
        return
      }

      const placeholder: AppMessage = {
        id: stream.message_id,
        session_id: '',
        role: 'assistant',
        content: '',
        artifacts: [],
        execution_id: stream.execution_id,
        tokens: 0,
        cost_usd: 0,
        latency_ms: 0,
        is_error: false,
        created_at: new Date().toISOString(),
      }
      setState({ status: 'streaming', assistant: placeholder, error: null })

      const es = new EventSource(publicAppAPI.streamUrl(stream.stream_url), {
        withCredentials: true,
      })
      esRef.current = es

      const applyDelta = (patch: Partial<AppMessage>) => {
        setState(s => (s.assistant ? { ...s, assistant: { ...s.assistant, ...patch } } : s))
      }

      es.addEventListener('token', ev => {
        try {
          const data = JSON.parse((ev as MessageEvent).data) as { text?: string }
          if (data.text) {
            setState(s =>
              s.assistant
                ? { ...s, assistant: { ...s.assistant, content: s.assistant.content + data.text } }
                : s,
            )
          }
        } catch {
          // ignore malformed frames
        }
      })

      es.addEventListener('artifact', ev => {
        try {
          const parsed = JSON.parse((ev as MessageEvent).data)
          // Runner emits `{node_id, artifact}`; older shape was the bare
          // artifact — support both.
          const artifact = parsed?.artifact ?? parsed
          if (artifact) {
            setState(s =>
              s.assistant
                ? { ...s, assistant: { ...s.assistant, artifacts: [...s.assistant.artifacts, artifact] } }
                : s,
            )
          }
        } catch {
          // ignore
        }
      })

      es.addEventListener('artifact_emitted', ev => {
        try {
          const parsed = JSON.parse((ev as MessageEvent).data)
          const artifact = parsed?.artifact ?? parsed
          if (artifact) {
            setState(s =>
              s.assistant
                ? { ...s, assistant: { ...s.assistant, artifacts: [...s.assistant.artifacts, artifact] } }
                : s,
            )
          }
        } catch {
          // ignore
        }
      })

      es.addEventListener('execution_completed', ev => {
        try {
          const data = JSON.parse((ev as MessageEvent).data)
          const output = data.output ?? {}
          // Prefer whatever text the runner emitted at the end.
          if (typeof output.content === 'string' && output.content) {
            applyDelta({ content: output.content })
          }
          if (Array.isArray(output.artifacts)) {
            applyDelta({ artifacts: output.artifacts })
          }
        } catch {
          // ignore
        }
      })

      es.addEventListener('execution_failed', ev => {
        let msg = 'Execution failed'
        try {
          const data = JSON.parse((ev as MessageEvent).data)
          if (typeof data.error === 'string') msg = data.error
        } catch {
          /* noop */
        }
        setState(s => ({
          status: 'error',
          assistant: s.assistant ? { ...s.assistant, is_error: true, content: msg } : null,
          error: msg,
        }))
      })

      es.addEventListener('stream_end', () => {
        setState(s => {
          if (s.assistant) onComplete(s.assistant)
          return { status: 'done', assistant: null, error: null }
        })
        es.close()
        esRef.current = null
      })

      es.onerror = () => {
        // EventSource retries automatically; only surface a persistent error.
        if (es.readyState === EventSource.CLOSED) {
          setState(s => ({
            status: 'error',
            assistant: s.assistant,
            error: 'Connection closed unexpectedly.',
          }))
        }
      }
    },
    [workspaceSlug, appSlug, onComplete],
  )

  const cancel = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
    setState(EMPTY)
  }, [])

  return { state, send, cancel }
}

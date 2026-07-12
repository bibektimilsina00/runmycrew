import { useCallback, useEffect, useRef, useState } from 'react'
import { publicAppAPI } from '../services/publicAppAPI'
import type { AppMessage } from '../types/publicAppTypes'

interface StreamState {
  status: 'idle' | 'sending' | 'streaming' | 'done' | 'error'
  assistant: AppMessage | null
  error: string | null
  /** Human label of the node currently executing ("Agent", "Slack"…). */
  activity: string | null
}

const EMPTY: StreamState = { status: 'idle', assistant: null, error: null, activity: null }

/** "action.agent" → "Agent", "trigger.chat_app" → "Chat App". */
function humanNodeType(t: unknown): string | null {
  if (typeof t !== 'string' || !t) return null
  const tail = t.split('.').pop() ?? ''
  return tail.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') || null
}

/** No events for this long while streaming → give up and say so. */
const STREAM_TIMEOUT_MS = 120_000

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
  const watchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Mirror of state.assistant so stream_end can hand the final message to
  // onComplete OUTSIDE a setState updater — side effects in updaters run
  // twice under StrictMode and duplicated every reply.
  const assistantRef = useRef<AppMessage | null>(null)

  useEffect(() => {
    return () => {
      esRef.current?.close()
      esRef.current = null
      if (watchdogRef.current) clearTimeout(watchdogRef.current)
    }
  }, [])

  const send = useCallback(
    async (message: string, formData?: Record<string, unknown>, sessionId?: string) => {
      esRef.current?.close()
      setState({ status: 'sending', assistant: null, error: null, activity: null })

      let stream: Awaited<ReturnType<typeof publicAppAPI.sendMessage>>
      try {
        stream = await publicAppAPI.sendMessage(workspaceSlug, appSlug, {
          message,
          form_data: formData,
          session_id: sessionId,
        })
      } catch (e) {
        setState({
          status: 'error',
          assistant: null,
          error: e instanceof Error ? e.message : 'Send failed',
          activity: null,
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
      assistantRef.current = placeholder
      setState({ status: 'streaming', assistant: placeholder, error: null, activity: null })

      // Editor test loop: when this tab was opened from the workflow
      // editor ("Run" on a chat-trigger graph), hand it each execution id
      // so it can attach its log panel to the run. Same-origin only.
      try {
        window.opener?.postMessage(
          { type: 'fuse-app-execution', executionId: stream.execution_id },
          window.location.origin,
        )
      } catch {
        /* opener gone or cross-origin — nothing to notify */
      }

      const es = new EventSource(publicAppAPI.streamUrl(stream.stream_url), {
        withCredentials: true,
      })
      esRef.current = es

      // A crashed worker or lost task means no events, ever — without a
      // watchdog the visitor stares at a spinner forever. Any event
      // (including heartbeats handled by EventSource) resets the clock.
      const armWatchdog = () => {
        if (watchdogRef.current) clearTimeout(watchdogRef.current)
        watchdogRef.current = setTimeout(() => {
          es.close()
          esRef.current = null
          const msg = 'The run timed out with no response. Please try again.'
          if (assistantRef.current) {
            assistantRef.current = {
              ...assistantRef.current,
              is_error: true,
              content: assistantRef.current.content || msg,
            }
          }
          const snapshot = assistantRef.current
          setState({ status: 'error', assistant: snapshot, error: msg, activity: null })
        }, STREAM_TIMEOUT_MS)
      }
      armWatchdog()
      es.addEventListener('stream_open', armWatchdog)

      es.addEventListener('node_started', ev => {
        armWatchdog()
        try {
          const data = JSON.parse((ev as MessageEvent).data) as { node_type?: string }
          const label = humanNodeType(data.node_type)
          // The trigger firing isn't interesting; show real work.
          if (label && !label.includes('Chat App')) {
            setState(s => (s.status === 'streaming' ? { ...s, activity: label } : s))
          }
        } catch {
          /* ignore */
        }
      })

      es.addEventListener('node_completed', () => armWatchdog())

      // Ref-first: the ref mutates synchronously with event arrival (setState
      // updaters are deferred, so syncing the ref inside them races
      // stream_end reading it), then state renders the snapshot.
      const patchAssistant = (patch: Partial<AppMessage>) => {
        if (!assistantRef.current) return
        assistantRef.current = { ...assistantRef.current, ...patch }
        const snapshot = assistantRef.current
        setState(s => ({ ...s, assistant: snapshot }))
      }

      // The engine emits `agent_chunk` frames with a `delta` field —
      // this hook listened for a `token`/`text` event that nothing ever
      // sent, so replies only appeared at execution_completed.
      es.addEventListener('agent_chunk', ev => {
        armWatchdog()
        try {
          const data = JSON.parse((ev as MessageEvent).data) as { delta?: string }
          if (data.delta && assistantRef.current) {
            patchAssistant({ content: assistantRef.current.content + data.delta })
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
          if (artifact && assistantRef.current) {
            patchAssistant({ artifacts: [...assistantRef.current.artifacts, artifact] })
          }
        } catch {
          // ignore
        }
      })

      es.addEventListener('artifact_emitted', ev => {
        try {
          const parsed = JSON.parse((ev as MessageEvent).data)
          const artifact = parsed?.artifact ?? parsed
          if (artifact && assistantRef.current) {
            patchAssistant({ artifacts: [...assistantRef.current.artifacts, artifact] })
          }
        } catch {
          // ignore
        }
      })

      es.addEventListener('execution_completed', ev => {
        try {
          const data = JSON.parse((ev as MessageEvent).data)
          const output = data.output ?? {}
          // Prefer whatever text the runner emitted at the end. Crew
          // terminals nest the round artifact under `result`.
          const finalText =
            typeof output.content === 'string' && output.content
              ? output.content
              : typeof output.result?.content === 'string' && output.result.content
                ? output.result.content
                : ''
          if (finalText) {
            patchAssistant({ content: finalText })
          }
          if (Array.isArray(output.artifacts)) {
            patchAssistant({ artifacts: output.artifacts })
          }
        } catch {
          // ignore
        }
      })

      es.addEventListener('execution_failed', ev => {
        if (watchdogRef.current) clearTimeout(watchdogRef.current)
        let msg = 'Execution failed'
        try {
          const data = JSON.parse((ev as MessageEvent).data)
          if (typeof data.error === 'string') msg = data.error
        } catch {
          /* noop */
        }
        if (assistantRef.current) {
          assistantRef.current = { ...assistantRef.current, is_error: true, content: msg }
        }
        const snapshot = assistantRef.current
        setState({ status: 'error', assistant: snapshot, error: msg, activity: null })
      })

      es.addEventListener('stream_end', () => {
        if (watchdogRef.current) clearTimeout(watchdogRef.current)
        const final = assistantRef.current
        assistantRef.current = null
        if (final) onComplete(final)
        setState({ status: 'done', assistant: null, error: null, activity: null })
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
            activity: null,
          }))
        }
      }
    },
    [workspaceSlug, appSlug, onComplete],
  )

  const cancel = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
    if (watchdogRef.current) clearTimeout(watchdogRef.current)
    setState(EMPTY)
  }, [])

  return { state, send, cancel }
}

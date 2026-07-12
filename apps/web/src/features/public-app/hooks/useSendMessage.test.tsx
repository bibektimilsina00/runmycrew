import { StrictMode, type ReactNode } from 'react'
import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useSendMessage } from './useSendMessage'
import { publicAppAPI } from '../services/publicAppAPI'

vi.mock('../services/publicAppAPI', () => ({
  publicAppAPI: {
    sendMessage: vi.fn(),
    streamUrl: vi.fn((p: string) => p),
  },
}))

/**
 * Controllable EventSource fake: tests push named SSE events into it and
 * the hook's listeners fire synchronously.
 */
class FakeEventSource {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSED = 2
  static instances: FakeEventSource[] = []

  readyState = FakeEventSource.OPEN
  url: string
  withCredentials: boolean
  onerror: ((ev: Event) => void) | null = null
  private listeners = new Map<string, Array<(ev: MessageEvent) => void>>()

  constructor(url: string, opts?: { withCredentials?: boolean }) {
    this.url = url
    this.withCredentials = opts?.withCredentials ?? false
    FakeEventSource.instances.push(this)
  }

  addEventListener(type: string, fn: (ev: MessageEvent) => void) {
    const list = this.listeners.get(type) ?? []
    list.push(fn)
    this.listeners.set(type, list)
  }

  close() {
    this.readyState = FakeEventSource.CLOSED
  }

  /** Push an SSE event; `data` is JSON-stringified like the real wire. */
  emit(type: string, data?: unknown) {
    const ev = new MessageEvent(type, {
      data: data === undefined ? undefined : JSON.stringify(data),
    })
    for (const fn of this.listeners.get(type) ?? []) fn(ev)
  }
}

const STREAM_OK = {
  message_id: 'msg-1',
  execution_id: 'exec-1',
  stream_url: '/api/v1/apps/ws/app/stream/exec-1',
}

function lastES(): FakeEventSource {
  const es = FakeEventSource.instances.at(-1)
  if (!es) throw new Error('no EventSource was opened')
  return es
}

beforeEach(() => {
  vi.stubGlobal('EventSource', FakeEventSource)
  FakeEventSource.instances = []
  vi.mocked(publicAppAPI.sendMessage).mockResolvedValue(STREAM_OK)
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

describe('useSendMessage — stream lifecycle', () => {
  it('accumulates token events into assistant content and completes once on stream_end', async () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() => useSendMessage('ws', 'app', onComplete))

    await act(() => result.current.send('hello'))
    const es = lastES()
    expect(result.current.state.status).toBe('streaming')

    act(() => {
      es.emit('agent_chunk', { delta: 'Hel' })
      es.emit('agent_chunk', { delta: 'lo ' })
      es.emit('agent_chunk', { delta: 'world' })
    })
    expect(result.current.state.assistant?.content).toBe('Hello world')

    act(() => es.emit('stream_end'))

    expect(onComplete).toHaveBeenCalledTimes(1)
    expect(onComplete).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'msg-1', content: 'Hello world', is_error: false }),
    )
    expect(result.current.state.status).toBe('done')
    expect(es.readyState).toBe(FakeEventSource.CLOSED)
  })

  it('execution_failed sets error state with the server message', async () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() => useSendMessage('ws', 'app', onComplete))

    await act(() => result.current.send('hello'))
    const es = lastES()

    act(() => es.emit('execution_failed', { error: 'Model quota exceeded' }))

    expect(result.current.state.status).toBe('error')
    expect(result.current.state.error).toBe('Model quota exceeded')
    expect(result.current.state.assistant).toEqual(
      expect.objectContaining({ is_error: true, content: 'Model quota exceeded' }),
    )
  })

  it('StrictMode double render: onComplete still fires exactly once per stream', async () => {
    const onComplete = vi.fn()
    const wrapper = ({ children }: { children: ReactNode }) => (
      <StrictMode>{children}</StrictMode>
    )
    const { result } = renderHook(() => useSendMessage('ws', 'app', onComplete), { wrapper })

    await act(() => result.current.send('hello'))
    const es = lastES()

    act(() => {
      es.emit('agent_chunk', { delta: 'reply' })
      es.emit('stream_end')
    })

    // The shipped bug: onComplete was called from inside a setState updater,
    // which StrictMode invokes twice — duplicating every assistant message.
    expect(onComplete).toHaveBeenCalledTimes(1)
    expect(onComplete).toHaveBeenCalledWith(expect.objectContaining({ content: 'reply' }))

    // A second turn completes exactly once more.
    await act(() => result.current.send('again'))
    act(() => {
      lastES().emit('agent_chunk', { delta: 'two' })
      lastES().emit('stream_end')
    })
    expect(onComplete).toHaveBeenCalledTimes(2)
    expect(onComplete).toHaveBeenLastCalledWith(expect.objectContaining({ content: 'two' }))
  })
})

describe('useSendMessage — ref-first ordering', () => {
  it('execution_failed immediately followed by stream_end hands the ERROR message to onComplete', async () => {
    const onComplete = vi.fn()
    const { result } = renderHook(() => useSendMessage('ws', 'app', onComplete))

    await act(() => result.current.send('hello'))
    const es = lastES()

    // The shipped regression: the failure was written via a deferred setState
    // updater, so stream_end (arriving in the same tick) read a stale ref and
    // delivered an empty/"No response produced" message instead of the error.
    act(() => {
      es.emit('execution_failed', { error: 'Node "Agent" crashed' })
      es.emit('stream_end')
    })

    expect(onComplete).toHaveBeenCalledTimes(1)
    expect(onComplete).toHaveBeenCalledWith(
      expect.objectContaining({ is_error: true, content: 'Node "Agent" crashed' }),
    )
  })
})

describe('useSendMessage — watchdog', () => {
  it('times out into error state and closes the EventSource when no events arrive', async () => {
    vi.useFakeTimers()
    const onComplete = vi.fn()
    const { result } = renderHook(() => useSendMessage('ws', 'app', onComplete))

    await act(() => result.current.send('hello'))
    const es = lastES()
    expect(result.current.state.status).toBe('streaming')

    act(() => {
      vi.advanceTimersByTime(120_000)
    })

    expect(result.current.state.status).toBe('error')
    expect(result.current.state.error).toMatch(/timed out/i)
    expect(es.readyState).toBe(FakeEventSource.CLOSED)
    expect(onComplete).not.toHaveBeenCalled()
  })

  it('events reset the watchdog clock', async () => {
    vi.useFakeTimers()
    const onComplete = vi.fn()
    const { result } = renderHook(() => useSendMessage('ws', 'app', onComplete))

    await act(() => result.current.send('hello'))
    const es = lastES()

    // Just before the deadline an event arrives — the clock re-arms.
    act(() => {
      vi.advanceTimersByTime(119_000)
      es.emit('agent_chunk', { delta: 'still alive' })
      vi.advanceTimersByTime(119_000)
    })
    expect(result.current.state.status).toBe('streaming')

    act(() => {
      vi.advanceTimersByTime(1_000)
    })
    expect(result.current.state.status).toBe('error')
  })
})

describe('useSendMessage — request shape', () => {
  it('sends session_id in the POST body', async () => {
    const { result } = renderHook(() => useSendMessage('ws', 'app', vi.fn()))

    await act(() => result.current.send('hi', { name: 'Ada' }, 'sess-42'))

    expect(publicAppAPI.sendMessage).toHaveBeenCalledWith('ws', 'app', {
      message: 'hi',
      form_data: { name: 'Ada' },
      session_id: 'sess-42',
    })
  })

  it('opens the EventSource with credentials on the resolved stream URL', async () => {
    const { result } = renderHook(() => useSendMessage('ws', 'app', vi.fn()))

    await act(() => result.current.send('hi'))

    const es = lastES()
    expect(publicAppAPI.streamUrl).toHaveBeenCalledWith(STREAM_OK.stream_url)
    expect(es.url).toBe(STREAM_OK.stream_url)
    expect(es.withCredentials).toBe(true)
  })
})

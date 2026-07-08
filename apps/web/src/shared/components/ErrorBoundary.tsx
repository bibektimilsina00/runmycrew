import { Component, type ReactNode } from 'react'

interface State {
  error: Error | null
}

interface Props {
  children: ReactNode
}

/**
 * Root error boundary. Prevents any downstream render crash from taking
 * the whole app blank-white. Shows the caught message + a reload button
 * so we always have a way out during dev.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error) {
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', error)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-screen w-screen flex-col items-center justify-center gap-4 bg-bg p-6 text-text">
          <h1 className="text-xl font-semibold">Something crashed while rendering.</h1>
          <pre className="max-w-2xl overflow-auto rounded border border-border-soft bg-surface p-4 text-xs text-text-mute">
            {this.state.error.message}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

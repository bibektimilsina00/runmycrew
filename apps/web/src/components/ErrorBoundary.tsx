import React from 'react'
import { useRouteError, isRouteErrorResponse, useNavigate } from 'react-router-dom'
import { AlertTriangle, RotateCcw, Home } from 'lucide-react'

// ── Route-level error element (used with React Router errorElement) ────────────

export function RouteError() {
  const error = useRouteError()
  const navigate = useNavigate()

  let title = 'Something went wrong'
  let message = 'An unexpected error occurred.'

  if (isRouteErrorResponse(error)) {
    if (error.status === 404) { title = 'Page not found'; message = 'The page you\'re looking for doesn\'t exist.' }
    else if (error.status === 403) { title = 'Access denied'; message = 'You don\'t have permission to view this page.' }
    else { title = `Error ${error.status}`; message = error.statusText || message }
  } else if (error instanceof Error) {
    message = error.message
  }

  return (
    <div className="flex h-full min-h-screen items-center justify-center bg-[var(--bg)] p-8">
      <div className="flex max-w-md flex-col items-center gap-4 text-center">
        <div className="flex size-14 items-center justify-center rounded-xl bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="size-7 text-red-400" />
        </div>
        <div>
          <h1 className="text-[18px] font-bold text-white">{title}</h1>
          <p className="mt-1 text-[13px] text-[var(--text-muted)]">{message}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-1.5 rounded-lg border border-[var(--border-default)] bg-[var(--surface-2)] px-3 py-2 text-[12px] font-medium text-white hover:bg-[var(--surface-3)] transition-colors"
          >
            <RotateCcw className="size-3.5" /> Reload
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-1.5 rounded-lg bg-white px-3 py-2 text-[12px] font-medium text-black hover:bg-gray-100 transition-colors"
          >
            <Home className="size-3.5" /> Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Class-based boundary for non-route component errors ───────────────────────

interface Props { children: React.ReactNode; fallback?: React.ReactNode }
interface State { hasError: boolean; error: Error | null }

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex h-full items-center justify-center p-8">
          <div className="flex max-w-sm flex-col items-center gap-3 text-center">
            <AlertTriangle className="size-8 text-red-400" />
            <div>
              <p className="text-[14px] font-semibold text-white">Component error</p>
              <p className="mt-1 text-[12px] text-[var(--text-muted)]">{this.state.error?.message}</p>
            </div>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="rounded-lg border border-[var(--border-default)] px-3 py-1.5 text-[12px] text-white hover:bg-[var(--surface-2)] transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

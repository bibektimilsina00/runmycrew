import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

/**
 * Landing page the backend redirects to after an OAuth callback
 * completes. Reads the stored return path from `sessionStorage` (set by
 * `ConnectModal` right before it navigated the tab away) and bounces
 * the user back to it — so a "Connect GitHub" click from inside the
 * inspector returns to the inspector, not to the dashboard.
 *
 * Refreshes the credential list on the way through so the newly-linked
 * connection shows up without a manual page reload.
 */
export function OAuthReturn() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  useEffect(() => {
    // Nudge any hook that keys off the credential list.
    qc.invalidateQueries({ queryKey: ['credentials'] })

    let target = '/'
    try {
      const stored = sessionStorage.getItem('oauth_return_to')
      // Guard against open-redirects — only same-origin relative paths.
      if (stored && stored.startsWith('/') && !stored.startsWith('//')) {
        target = stored
      }
      sessionStorage.removeItem('oauth_return_to')
    } catch { /* sessionStorage blocked — fall back to dashboard */ }

    navigate(target, { replace: true })
  }, [navigate, qc])

  return (
    <div className="flex h-screen items-center justify-center bg-[var(--bg)]">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--surface-2)] border-t-[var(--accent)]" />
        <span className="font-mono text-[12px] text-[var(--text-mute)]">Finishing connection…</span>
      </div>
    </div>
  )
}

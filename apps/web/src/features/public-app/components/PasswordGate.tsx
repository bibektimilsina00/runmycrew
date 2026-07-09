import { useState } from 'react'
import { Lock, Loader2 } from 'lucide-react'
import axios from 'axios'
import type { PublicApp } from '../types/publicAppTypes'

interface PasswordGateProps {
  app: PublicApp
  workspaceSlug: string
  appSlug: string
  onUnlocked: () => void
}

/**
 * Centered password prompt shown when auth_mode = password. Sets an
 * HttpOnly unlock cookie on success; the parent then re-runs the
 * session query.
 */
export function PasswordGate({ app, workspaceSlug, appSlug, onUnlocked }: PasswordGateProps) {
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!password.trim()) return
    setBusy(true)
    setError(null)
    try {
      const base = import.meta.env.VITE_API_URL || '/api/v1'
      await axios.post(
        `${base}/apps/${workspaceSlug}/${appSlug}/unlock`,
        { password },
        { withCredentials: true },
      )
      onUnlocked()
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.status === 429) {
        setError('Too many attempts. Try again in a minute.')
      } else {
        setError('Wrong password.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0b0b0f] px-6">
      <div className="w-full max-w-[380px] rounded-[16px] border border-white/8 bg-white/[0.02] p-6 text-center shadow-[0_20px_60px_-20px_rgba(0,0,0,0.6)]">
        <div
          className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-[12px]"
          style={{
            background: 'color-mix(in oklab, var(--app-accent, #8b5cf6) 18%, transparent)',
            color: 'var(--app-accent, #8b5cf6)',
          }}
        >
          <Lock size={18} />
        </div>
        <h1 className="text-[19px] font-semibold text-white">{app.title}</h1>
        <p className="mt-1 text-[12.5px] text-white/50">
          This app is password-gated. Enter the password to continue.
        </p>
        <form
          className="mt-5 flex flex-col gap-2"
          onSubmit={e => {
            e.preventDefault()
            void submit()
          }}
        >
          <input
            type="password"
            value={password}
            autoFocus
            onChange={e => setPassword(e.target.value)}
            placeholder="Password"
            aria-label="Password"
            className="h-10 w-full rounded-[9px] border border-white/10 bg-white/[0.03] px-3 text-[14px] text-white placeholder:text-white/30 focus:border-white/25 focus:outline-none"
          />
          {error && <p className="text-[12px] text-red-400/80">{error}</p>}
          <button
            type="submit"
            disabled={busy || !password.trim()}
            className="mt-1 flex h-10 w-full items-center justify-center gap-2 rounded-[9px] text-[13.5px] font-medium text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            style={{ background: 'var(--app-accent, #8b5cf6)' }}
          >
            {busy && <Loader2 size={13} className="animate-spin" />}
            Unlock
          </button>
        </form>
      </div>
    </div>
  )
}

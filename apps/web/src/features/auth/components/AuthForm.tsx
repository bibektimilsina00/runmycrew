import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Lock, Eye, EyeOff, Mail } from 'lucide-react'
import { Icons } from '@/shared/components/icons'
import { FormField, Input, useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useAuth } from '../hooks/useAuth'

type Mode = 'login' | 'signup'

interface AuthFormProps { mode: Mode }

const COPY = {
  login: {
    heading: 'Log in to Fuse',
    sub: 'Welcome back. Connect your tools and keep things running.',
    verb: 'Continue with',
    primary: 'Continue with email',
    togglePrompt: 'New to Fuse?',
    toggleLabel: 'Create an account',
    toggleHref: APP_ROUTES.REGISTER,
    legal: 'By continuing, you agree to our',
  },
  signup: {
    heading: 'Create your account',
    sub: 'Start automating in minutes — no credit card required.',
    verb: 'Continue with',
    primary: 'Create account',
    togglePrompt: 'Already have an account?',
    toggleLabel: 'Log in',
    toggleHref: APP_ROUTES.LOGIN,
    legal: 'By creating an account, you agree to our',
  },
} as const

/**
 * Shared auth card — drives both Login and Register from one component.
 * Tokens, weights, and radii mirror the marketing site so the handoff
 * from `fuse.bibektimilsina.tech` → `app.*` feels continuous.
 */
export function AuthForm({ mode }: AuthFormProps) {
  const copy = COPY[mode]
  const { login, register, isLoading } = useAuth()
  const navigate = useNavigate()
  const { toast } = useToast()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setErr(null)
    if (!email) return setErr('Enter your email')
    if (!password) return setErr('Enter your password')
    if (mode === 'signup' && password.length < 8) {
      return setErr('Password must be at least 8 characters')
    }

    try {
      if (mode === 'login') {
        await login({ email, password })
        toast('Welcome back', { variant: 'ok' })
      } else {
        await register({ email, password })
        toast('Account created', { variant: 'ok', description: 'Your workspace is ready.' })
      }
      navigate(APP_ROUTES.DASHBOARD)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Something went wrong')
    }
  }

  const ssoSoon = () =>
    toast('Coming soon', {
      variant: 'warn',
      description: 'OAuth providers are wired but not enabled yet — use email below.',
    })

  const goGoogle = () => {
    // Full-page redirect so the backend can set the session in its own
    // response — we never see Google's consent page inside an AJAX call.
    // `VITE_API_URL` is `/api/v1` in prod (same-origin via Caddy) and
    // e.g. `http://localhost:8000/api/v1` in dev.
    const base = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/+$/, '')
    const next = encodeURIComponent('/dashboard')
    window.location.assign(`${base}/auth/google/start?next=${next}`)
  }

  return (
    <>
      {/* Brand mark */}
      <div className="mb-[22px] flex justify-center">
        <Icons.FuseMark style={{ width: 40, height: 40, color: 'var(--accent)' }} />
      </div>

      <h1 className="m-0 text-center text-[28px] font-[560] leading-[1.1] tracking-[-0.022em] text-[var(--text)]">
        {copy.heading}
      </h1>
      <p className="mt-3 text-center text-[14.5px] leading-[1.55] text-[var(--text-mute)]">
        {copy.sub}
      </p>

      {/* SSO triplet — Google is live; GitHub + Microsoft show a toast
          until their backend providers ship. */}
      <div className="mt-[30px] flex flex-col gap-2.5">
        <SsoButton onClick={goGoogle}>
          <GoogleIcon /> {copy.verb} Google
        </SsoButton>
        <SsoButton onClick={ssoSoon}>
          <GithubIcon /> {copy.verb} GitHub
        </SsoButton>
        <SsoButton onClick={ssoSoon}>
          <MicrosoftIcon /> {copy.verb} Microsoft
        </SsoButton>
      </div>

      {/* Divider */}
      <div className="my-[22px] flex items-center gap-3.5">
        <span className="h-px flex-1 bg-white/[0.08]" />
        <span className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[var(--text-dim)]">OR</span>
        <span className="h-px flex-1 bg-white/[0.08]" />
      </div>

      <form onSubmit={submit} className="flex flex-col gap-3.5">
        <FormField label="Email">
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            autoComplete="email"
            disabled={isLoading}
            leftIcon={<Mail strokeWidth={1.8} />}
            className="h-11 border-white/[0.14] bg-[var(--surface-2)] hover:border-white/[0.22] focus-within:border-[var(--accent)]"
          />
        </FormField>

        <FormField label={mode === 'signup' ? 'Work password' : 'Password'}>
          <Input
            type={showPwd ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={mode === 'signup' ? 'Create a password' : 'Your password'}
            autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            disabled={isLoading}
            leftIcon={<Lock strokeWidth={1.8} />}
            className="h-11 border-white/[0.14] bg-[var(--surface-2)] hover:border-white/[0.22] focus-within:border-[var(--accent)]"
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPwd((v) => !v)}
                className="rounded-md p-0.5 text-[var(--text-faint)] transition-colors hover:bg-white/[0.06] hover:text-[var(--text)]"
                aria-label={showPwd ? 'Hide password' : 'Show password'}
              >
                {showPwd ? <EyeOff /> : <Eye />}
              </button>
            }
          />
        </FormField>

        {mode === 'login' && (
          <div className="mt-3 text-right">
            <Link
              to={APP_ROUTES.FORGOT_PASSWORD}
              className="text-[12.5px] text-[var(--text-mute)] transition-colors hover:text-[var(--text)]"
            >
              Forgot password?
            </Link>
          </div>
        )}

        {err && (
          <div className="mt-3 flex items-center gap-2 rounded-md border border-[color-mix(in_oklab,var(--err)_25%,transparent)] bg-[color-mix(in_oklab,var(--err)_12%,transparent)] px-3 py-2 text-[12.5px] text-[var(--err)]">
            <span className="h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-[var(--err)]" />
            <span>{err}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="mt-4 inline-flex h-[42px] w-full items-center justify-center gap-[7px] rounded-[8px] border-none bg-[var(--accent)] px-[16px] text-[14px] font-semibold text-white transition-[filter] hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? 'Please wait…' : copy.primary}
          {!isLoading && <ArrowRight className="h-[15px] w-[15px]" strokeWidth={2.2} />}
        </button>
      </form>

      <button
        type="button"
        onClick={ssoSoon}
        className="mt-2.5 inline-flex h-[40px] w-full items-center justify-center gap-2 rounded-[8px] border border-white/[0.14] bg-white/[0.05] px-3 text-[13px] font-medium text-[var(--text)] transition-colors hover:border-white/[0.22] hover:bg-white/[0.09]"
      >
        <Lock className="h-[14px] w-[14px]" strokeWidth={1.8} />
        Single sign-on (SAML)
      </button>

      <div className="mt-[26px] text-center text-[13.5px] text-[var(--text-faint)]">
        {copy.togglePrompt}{' '}
        <Link
          to={copy.toggleHref}
          className="ml-0.5 cursor-pointer border-none bg-transparent p-0 text-[13.5px] font-semibold text-[var(--accent)] transition-[text-decoration] hover:underline"
        >
          {copy.toggleLabel}
        </Link>
      </div>

      <p className="mx-auto mt-7 max-w-[300px] text-center text-[11.5px] leading-[1.6] text-[var(--text-dim)]">
        {copy.legal}{' '}
        <a href="#" className="text-[var(--text-faint)] transition-colors hover:text-[var(--text-mute)]">
          Terms
        </a>{' '}
        and{' '}
        <a href="#" className="text-[var(--text-faint)] transition-colors hover:text-[var(--text-mute)]">
          Privacy Policy
        </a>
        .
      </p>
    </>
  )
}

/* ─── Bits ─────────────────────────────────────────────────────────── */

function SsoButton({
  children,
  onClick,
}: {
  children: React.ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-[11px] rounded-[8px] border border-white/[0.14] bg-white/[0.05] px-[14px] py-[10px] text-left text-[14px] font-medium text-[var(--text)] transition-colors hover:border-white/[0.22] hover:bg-white/[0.09]"
    >
      {children}
    </button>
  )
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" className="shrink-0">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  )
}

function GithubIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="#fff" className="shrink-0">
      <path d="M12 1C5.92 1 1 5.92 1 12c0 4.86 3.15 8.98 7.52 10.44.55.1.75-.24.75-.53 0-.26-.01-.96-.01-1.88-3.06.66-3.71-1.48-3.71-1.48-.5-1.27-1.22-1.61-1.22-1.61-1-.68.08-.67.08-.67 1.1.08 1.68 1.13 1.68 1.13.98 1.68 2.57 1.19 3.2.91.1-.71.38-1.19.69-1.46-2.44-.28-5.01-1.22-5.01-5.43 0-1.2.43-2.18 1.13-2.95-.11-.28-.49-1.4.11-2.91 0 0 .92-.3 3.02 1.13.88-.24 1.82-.36 2.76-.37.94 0 1.88.13 2.76.37 2.1-1.43 3.02-1.13 3.02-1.13.6 1.51.22 2.63.11 2.91.7.77 1.13 1.75 1.13 2.95 0 4.22-2.58 5.15-5.03 5.42.4.34.75 1.01.75 2.04 0 1.47-.01 2.66-.01 3.02 0 .29.2.64.76.53C19.85 20.98 23 16.86 23 12c0-6.08-4.92-11-11-11z" />
    </svg>
  )
}

function MicrosoftIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" className="shrink-0">
      <rect x="1"  y="1"  width="10" height="10" fill="#F25022" />
      <rect x="13" y="1"  width="10" height="10" fill="#7FBA00" />
      <rect x="1"  y="13" width="10" height="10" fill="#00A4EF" />
      <rect x="13" y="13" width="10" height="10" fill="#FFB900" />
    </svg>
  )
}

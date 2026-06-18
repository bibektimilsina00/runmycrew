import { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AuthShell } from '../components/AuthShell'
import { AuthForm } from '../components/AuthForm'
import { useAuthStore } from '../store/authStore'
import { useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'

export function Login() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const setToken = useAuthStore((s) => s.setToken)
  const { toast } = useToast()
  // useEffect runs twice under React 18 StrictMode — guard so we don't
  // double-toast or double-navigate.
  const handled = useRef(false)

  useEffect(() => {
    if (handled.current) return
    const token = params.get('token')
    const errorCode = params.get('error')
    const next = params.get('next') || APP_ROUTES.DASHBOARD

    if (token) {
      handled.current = true
      setToken(token)
      // Drop the query so the JWT is never left in the URL bar or
      // history — Login.tsx is the only page that needs to see it.
      setParams({}, { replace: true })
      toast('Welcome back', { variant: 'ok' })
      navigate(next.startsWith('/') ? next : APP_ROUTES.DASHBOARD, { replace: true })
      return
    }

    if (errorCode) {
      handled.current = true
      setParams({}, { replace: true })
      toast('Sign-in failed', {
        variant: 'err',
        description: errorCode === 'google_cancelled' ? 'You cancelled the Google flow.' : errorCode,
      })
    }
  }, [params, setParams, setToken, navigate, toast])

  return (
    <AuthShell>
      <AuthForm mode="login" />
    </AuthShell>
  )
}

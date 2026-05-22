import { useState, type FormEvent } from 'react'
import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, Input, Checkbox, FormField, Card, useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useAuth } from '../hooks/useAuth'

/**
 * LoginForm provides a premium login user interface matching the V2 specifications.
 */
export function LoginForm() {
  const { login, isLoading } = useAuth()
  const navigate = useNavigate()
  const { toast } = useToast()
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (!email || !password) {
      setLocalError('Please fill in all fields')
      return
    }

    try {
      await login({ email, password })
      toast('Logged in successfully', {
        variant: 'ok',
        description: 'Welcome back to your workspace.',
      })
      navigate(APP_ROUTES.DASHBOARD)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Incorrect email or password'
      setLocalError(message)
    }
  }

  return (
    <Card className="w-full max-w-[400px] bg-bg2/80 backdrop-blur-md border border-border-faint shadow-panel" padding="lg">
      <div className="flex flex-col gap-2 mb-6">
        <h2 className="text-xl font-semibold text-text tracking-tight">Welcome back</h2>
        <p className="text-xs text-text-mute">
          Enter your credentials to access your workspace.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {localError && (
          <div className="p-3 text-xs bg-[oklch(0.35_0.12_20/0.15)] border border-[oklch(0.45_0.15_20/0.2)] text-err rounded-[8px] flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-err shrink-0 animate-pulse" />
            <span>{localError}</span>
          </div>
        )}

        <FormField label="Email Address" required>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@company.com"
            leftIcon={<Mail />}
            disabled={isLoading}
            autoComplete="email"
          />
        </FormField>

        <FormField label="Password" required>
          <Input
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            leftIcon={<Lock />}
            disabled={isLoading}
            autoComplete="current-password"
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="hover:text-text focus:outline-none transition-colors"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            }
          />
        </FormField>

        <div className="flex items-center justify-between mt-1 mb-2">
          <Checkbox
            label="Remember me"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
          />
          <Link
            to={APP_ROUTES.FORGOT_PASSWORD}
            className="text-[12px] text-text-mute hover:text-text hover:underline transition-all cursor-pointer font-medium text-right"
          >
            Forgot password?
          </Link>
        </div>

        <Button
          type="submit"
          variant="primary"
          className="w-full justify-center h-10 mt-1 cursor-pointer"
          loading={isLoading}
        >
          Sign In
        </Button>
      </form>

      <div className="mt-6 pt-4 border-t border-border-faint text-center text-[12px] text-text-mute">
        Don't have an account?{' '}
        <Link
          to={APP_ROUTES.REGISTER}
          className="font-medium text-text hover:underline cursor-pointer"
        >
          Create account
        </Link>
      </div>
    </Card>
  )
}




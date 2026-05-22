import { useState, type FormEvent } from 'react'
import { Mail, Lock, User as UserIcon, Eye, EyeOff, Check, X } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, Input, FormField, Card, useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useAuth } from '../hooks/useAuth'

/**
 * RegisterForm provides a premium sign-up interface matching the V2 specifications.
 */
export function RegisterForm() {
  const { register, isLoading } = useAuth()
  const navigate = useNavigate()
  const { toast } = useToast()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  // Password requirements derived from state
  const reqs = {
    length: password.length >= 8,
    numberOrSymbol: /[0-9!@#$%^&*(),.?":{}|<>]/.test(password),
    match: password.length > 0 && password === confirmPassword,
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (!email || !password || !confirmPassword) {
      setLocalError('Please fill in all required fields')
      return
    }

    if (!reqs.length || !reqs.numberOrSymbol) {
      setLocalError('Please satisfy all password strength requirements')
      return
    }

    if (!reqs.match) {
      setLocalError('Passwords do not match')
      return
    }

    try {
      await register({
        email,
        password,
        full_name: fullName || undefined,
      })
      toast('Account created', {
        variant: 'ok',
        description: 'Your workspace has been initialized successfully.',
      })
      navigate(APP_ROUTES.DASHBOARD)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed'
      setLocalError(message)
    }
  }

  return (
    <Card className="w-full max-w-[400px] bg-bg2/80 backdrop-blur-md border border-border-faint shadow-panel" padding="lg">
      <div className="flex flex-col gap-2 mb-6">
        <h2 className="text-xl font-semibold text-text tracking-tight">Create an account</h2>
        <p className="text-xs text-text-mute">
          Enter your details to create your workspace.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {localError && (
          <div className="p-3 text-xs bg-[oklch(0.35_0.12_20/0.15)] border border-[oklch(0.45_0.15_20/0.2)] text-err rounded-[8px] flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-err shrink-0 animate-pulse" />
            <span>{localError}</span>
          </div>
        )}

        <FormField label="Full Name">
          <Input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="John Doe"
            leftIcon={<UserIcon />}
            disabled={isLoading}
            autoComplete="name"
          />
        </FormField>

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
            placeholder="Min. 8 characters"
            leftIcon={<Lock />}
            disabled={isLoading}
            autoComplete="new-password"
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

        <FormField label="Confirm Password" required>
          <Input
            type={showPassword ? 'text' : 'password'}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter password"
            leftIcon={<Lock />}
            disabled={isLoading}
            autoComplete="new-password"
          />
        </FormField>

        {/* Requirements checklist */}
        <div className="flex flex-col gap-1.5 p-2.5 bg-bg/50 border border-border-faint rounded-[8px] mt-1 text-[11px]">
          <div className="flex items-center gap-1.5 text-text-mute font-medium mb-0.5">Password requirements:</div>
          <div className="flex items-center gap-2">
            <span className={`flex items-center justify-center w-3.5 h-3.5 rounded-full ${reqs.length ? 'bg-ok/10 text-ok' : 'bg-text-faint/10 text-text-faint'}`}>
              {reqs.length ? <Check size={10} strokeWidth={3} /> : <X size={10} strokeWidth={3} />}
            </span>
            <span className={reqs.length ? 'text-text' : 'text-text-faint'}>At least 8 characters</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`flex items-center justify-center w-3.5 h-3.5 rounded-full ${reqs.numberOrSymbol ? 'bg-ok/10 text-ok' : 'bg-text-faint/10 text-text-faint'}`}>
              {reqs.numberOrSymbol ? <Check size={10} strokeWidth={3} /> : <X size={10} strokeWidth={3} />}
            </span>
            <span className={reqs.numberOrSymbol ? 'text-text' : 'text-text-faint'}>Contains a number or symbol</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`flex items-center justify-center w-3.5 h-3.5 rounded-full ${reqs.match ? 'bg-ok/10 text-ok' : 'bg-text-faint/10 text-text-faint'}`}>
              {reqs.match ? <Check size={10} strokeWidth={3} /> : <X size={10} strokeWidth={3} />}
            </span>
            <span className={reqs.match ? 'text-text' : 'text-text-faint'}>Passwords match</span>
          </div>
        </div>

        <Button
          type="submit"
          variant="primary"
          className="w-full justify-center h-10 mt-2 cursor-pointer"
          loading={isLoading}
        >
          Create Account
        </Button>
      </form>

      <div className="mt-6 pt-4 border-t border-border-faint text-center text-[12px] text-text-mute">
        Already have an account?{' '}
        <Link
          to={APP_ROUTES.LOGIN}
          className="font-medium text-text hover:underline cursor-pointer"
        >
          Sign in
        </Link>
      </div>
    </Card>
  )
}




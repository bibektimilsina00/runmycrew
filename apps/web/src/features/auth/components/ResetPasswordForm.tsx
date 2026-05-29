import { useState, type FormEvent } from 'react'
import { Lock, Eye, EyeOff, Check, X, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { Button, Input, FormField, Card, useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useAuth } from '../hooks/useAuth'

/**
 * ResetPasswordForm handles entering and submitting the new password using the token from the email.
 */
export function ResetPasswordForm() {
  const { resetPassword, isLoading } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitted, setSubmitted] = useState(false)
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

    if (!token) {
      setLocalError('Missing password reset token.')
      return
    }

    if (!password || !confirmPassword) {
      setLocalError('Please fill in all fields')
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
      await resetPassword({
        token,
        new_password: password,
      })
      toast('Password reset successfully', {
        variant: 'ok',
        description: 'You can now sign in with your new password.',
      })
      setSubmitted(true)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reset password'
      setLocalError(message)
    }
  }

  if (!token) {
    return (
      <Card className="w-full max-w-[400px] bg-bg2/80 backdrop-blur-md border border-border-faint shadow-panel text-center" padding="lg">
        <div className="flex flex-col items-center gap-4 mb-6">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-err/10 text-err animate-bounce">
            <AlertTriangle size={24} />
          </div>
          <div className="flex flex-col gap-2">
            <h2 className="text-xl font-semibold text-text tracking-tight">Invalid Link</h2>
            <p className="text-xs text-text-mute leading-relaxed">
              The password reset token is missing or invalid. Please request a new recovery link.
            </p>
          </div>
        </div>

        <Link to={APP_ROUTES.FORGOT_PASSWORD} className="inline-flex w-full">
          <Button variant="primary" className="w-full justify-center h-10 cursor-pointer">
            Request New Link
          </Button>
        </Link>
      </Card>
    )
  }

  if (submitted) {
    return (
      <Card className="w-full max-w-[400px] bg-bg2/80 backdrop-blur-md border border-border-faint shadow-panel text-center" padding="lg">
        <div className="flex flex-col items-center gap-4 mb-6">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-ok/10 text-ok animate-pulse">
            <CheckCircle2 size={24} />
          </div>
          <div className="flex flex-col gap-2">
            <h2 className="text-xl font-semibold text-text tracking-tight">Password Reset</h2>
            <p className="text-xs text-text-mute leading-relaxed">
              Your password has been successfully updated.
            </p>
          </div>
        </div>

        <Button
          variant="primary"
          className="w-full justify-center h-10 cursor-pointer"
          onClick={() => navigate(APP_ROUTES.LOGIN)}
        >
          Sign In Now
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-[400px] bg-bg2/80 backdrop-blur-md border border-border-faint shadow-panel" padding="lg">
      <div className="flex flex-col gap-2 mb-6">
        <h2 className="text-xl font-semibold text-text tracking-tight">Set new password</h2>
        <p className="text-xs text-text-mute">
          Please enter and confirm your new account password.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {localError && (
          <div className="p-3 text-xs bg-[oklch(0.35_0.12_20/0.15)] border border-[oklch(0.45_0.15_20/0.2)] text-err rounded-[8px] flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-err shrink-0 animate-pulse" />
            <span>{localError}</span>
          </div>
        )}

        <FormField label="New Password" required>
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

        <FormField label="Confirm New Password" required>
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
          Reset Password
        </Button>
      </form>
    </Card>
  )
}


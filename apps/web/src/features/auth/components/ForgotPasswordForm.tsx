import { useState, type FormEvent } from 'react'
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button, Input, FormField, Card, useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useAuth } from '../hooks/useAuth'

/**
 * ForgotPasswordForm provides a recovery link initiation interface matching the V2 specifications.
 */
export function ForgotPasswordForm() {
  const { forgotPassword, isLoading } = useAuth()
  const { toast } = useToast()
  
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (!email) {
      setLocalError('Please enter your email address')
      return
    }

    try {
      await forgotPassword({ email })
      toast('Recovery link sent', {
        variant: 'ok',
        description: 'Please check your email inbox for instructions.',
      })
      setSubmitted(true)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong'
      setLocalError(message)
    }
  }

  if (submitted) {
    return (
      <Card className="w-full max-w-[400px] bg-bg2/80 backdrop-blur-md border border-border-faint shadow-panel text-center" padding="lg">
        <div className="flex flex-col items-center gap-4 mb-6">
          <div className="flex items-center justify-center w-12 h-12 rounded-full bg-ok/10 text-ok animate-pulse">
            <CheckCircle2 size={24} />
          </div>
          <div className="flex flex-col gap-2">
            <h2 className="text-xl font-semibold text-text tracking-tight">Check your email</h2>
            <p className="text-xs text-text-mute leading-relaxed">
              If an account is registered with <strong className="text-text">{email}</strong>, we have sent instructions to reset your password.
            </p>
          </div>
        </div>

        <Link to={APP_ROUTES.LOGIN} className="inline-flex w-full">
          <Button variant="secondary" className="w-full justify-center h-10 cursor-pointer">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Sign In
          </Button>
        </Link>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-[400px] bg-bg2/80 backdrop-blur-md border border-border-faint shadow-panel" padding="lg">
      <div className="flex flex-col gap-2 mb-6">
        <h2 className="text-xl font-semibold text-text tracking-tight">Reset password</h2>
        <p className="text-xs text-text-mute">
          Enter your email and we'll send you a link to reset your password.
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

        <Button
          type="submit"
          variant="primary"
          className="w-full justify-center h-10 mt-1 cursor-pointer"
          loading={isLoading}
        >
          Send Recovery Link
        </Button>
      </form>

      <div className="mt-6 pt-4 border-t border-border-faint text-center">
        <Link
          to={APP_ROUTES.LOGIN}
          className="inline-flex items-center gap-1.5 text-[12px] font-medium text-text hover:underline cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Sign In
        </Link>
      </div>
    </Card>
  )
}


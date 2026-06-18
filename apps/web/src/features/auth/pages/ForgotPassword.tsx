import { AuthShell } from '../components/AuthShell'
import { ForgotPasswordForm } from '../components/ForgotPasswordForm'

export function ForgotPassword() {
  return (
    <AuthShell backLabel="Back to login">
      <ForgotPasswordForm />
    </AuthShell>
  )
}

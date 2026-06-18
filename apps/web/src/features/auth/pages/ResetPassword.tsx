import { AuthShell } from '../components/AuthShell'
import { ResetPasswordForm } from '../components/ResetPasswordForm'

export function ResetPassword() {
  return (
    <AuthShell backLabel="Back to login">
      <ResetPasswordForm />
    </AuthShell>
  )
}

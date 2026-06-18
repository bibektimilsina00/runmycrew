import { AuthShell } from '../components/AuthShell'
import { AuthForm } from '../components/AuthForm'

export function Register() {
  return (
    <AuthShell>
      <AuthForm mode="signup" />
    </AuthShell>
  )
}

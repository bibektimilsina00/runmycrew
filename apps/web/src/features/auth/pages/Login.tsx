import { AuthShell } from '../components/AuthShell'
import { AuthForm } from '../components/AuthForm'

export function Login() {
  return (
    <AuthShell>
      <AuthForm mode="login" />
    </AuthShell>
  )
}

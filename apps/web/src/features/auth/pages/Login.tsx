import { LoginForm } from '../components/LoginForm'

/**
 * Login page providing the centered authorization panel.
 */
export function Login() {
  return (
    <div className="min-h-screen w-screen bg-bg flex items-center justify-center relative px-4 overflow-hidden">
      {/* Background Dot Grid */}
      <div className="dot-grid" />

      {/*background glowing accent */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-[400px] z-10">
        <LoginForm />
      </div>
    </div>
  )
}


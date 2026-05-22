import { ResetPasswordForm } from '../components/ResetPasswordForm'

/**
 * ResetPassword page providing the centered new password entry panel.
 */
export function ResetPassword() {
  return (
    <div className="min-h-screen w-screen bg-bg flex items-center justify-center relative px-4 overflow-hidden">
      {/* Background Dot Grid */}
      <div className="dot-grid" />
      
      {/* Premium design background glowing accent */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-[400px] z-10">
        <ResetPasswordForm />
      </div>
    </div>
  )
}

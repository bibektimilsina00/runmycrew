import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { APP_ROUTES } from '@/shared/constants/routes'
import { Spinner } from './Spinner'

/**
 * Route guard component for authentication protection.
 * Redirects to `/login` if session is not authenticated.
 */
export function ProtectedRoute() {
  const { isAuthenticated, isRestoringSession } = useAuth()

  if (isRestoringSession) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-bg">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to={APP_ROUTES.LOGIN} replace />
  }

  return <Outlet />
}


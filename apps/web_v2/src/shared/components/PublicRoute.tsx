import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { APP_ROUTES } from '@/shared/constants/routes'
import { Spinner } from './Spinner'

/**
 * Route guard component for public-only authentication views.
 * Redirects to `/dashboard` if user is already logged in.
 */
export function PublicRoute() {
  const { isAuthenticated, isRestoringSession } = useAuth()

  if (isRestoringSession) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-bg">
        <Spinner size="lg" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to={APP_ROUTES.DASHBOARD} replace />
  }

  return <Outlet />
}


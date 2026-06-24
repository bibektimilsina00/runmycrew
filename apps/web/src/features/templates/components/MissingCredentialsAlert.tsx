import { useNavigate } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { Button } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'

/**
 * Inline alert shown above the Install button on the template detail
 * page when the user's workspace is missing one or more integrations
 * the template needs at runtime.
 *
 * `missing` is the subset of the template's `credentials_required` /
 * `tools_required` lists that the user hasn't connected yet. Empty
 * `missing` → render nothing so the alert disappears the moment the
 * last integration is added.
 */

interface MissingCredentialsAlertProps {
  missing: string[]
}

export function MissingCredentialsAlert({ missing }: MissingCredentialsAlertProps) {
  const navigate = useNavigate()
  if (!missing.length) return null

  return (
    <div className="flex flex-col gap-3.5 rounded-[10px] border border-[var(--warn)]/40 bg-[var(--warn)]/8 p-5">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-[18px] w-[18px] shrink-0 text-[var(--warn)]" />
        <div className="flex flex-col gap-1.5">
          <span className="text-[15px] font-semibold text-[var(--text)] tracking-[-0.01em]">
            Connect required integrations
          </span>
          <span className="text-[13.5px] leading-[1.6] text-[var(--text-mute)]">
            This template uses{' '}
            <span className="font-semibold text-[var(--text)]">
              {missing.join(', ')}
            </span>
            . Connect them in Connections so the workflow can run.
          </span>
        </div>
      </div>
      <div>
        <Button
          size="sm"
          variant="outline"
          onClick={() => navigate(APP_ROUTES.CONNECTIONS)}
        >
          Open Connections
        </Button>
      </div>
    </div>
  )
}

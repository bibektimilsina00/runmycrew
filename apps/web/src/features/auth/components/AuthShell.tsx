import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Icons } from '@/shared/components/icons'
import type { ReactNode } from 'react'

interface AuthShellProps {
  /** Center card content — login form / signup form / reset card. */
  children: ReactNode
  /** Override the "Back to home" link target. Default `/login` or `/register`
   *  is wrong for the marketing site — we don't host it on this app yet, so
   *  the link falls back to the login page itself. */
  backHref?: string
  backLabel?: string
}

/**
 * Shared chrome for every authenticated-or-not page (`/login`,
 * `/register`, `/forgot-password`, `/reset-password`). Owns:
 *
 *   - Ambient grid + accent radial wash (matches the marketing hero).
 *   - Top brand bar with mark + "Back to home" link.
 *   - Centered 392px column for the actual card.
 *
 * The shell is intentionally minimal — every auth page composes its own
 * card content. Backgrounds + brand stay identical across the flow so
 * users feel like they're moving inside a single surface, not jumping
 * between pages.
 */
export function AuthShell({ children, backHref = '/login', backLabel = 'Back to home' }: AuthShellProps) {
  return (
    <div className="relative flex min-h-screen w-full flex-col overflow-hidden bg-[var(--bg)] text-[var(--text)]">
      {/* Backdrop: grid + accent halo */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 [mask-image:radial-gradient(ellipse_80%_60%_at_50%_0%,#000,transparent_72%)] [-webkit-mask-image:radial-gradient(ellipse_80%_60%_at_50%_0%,#000,transparent_72%)]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-[-220px] h-[520px] w-[900px] -translate-x-1/2 bg-[radial-gradient(ellipse_at_center,color-mix(in_oklab,var(--accent)_18%,transparent),transparent_68%)] blur-2xl"
      />

      {/* Top bar */}
      <header className="relative z-10 mx-auto flex h-16 w-full max-w-[1280px] items-center px-7">
        <Link to="/" className="flex items-center gap-[9px]">
          <Icons.FuseMark style={{ width: 24, height: 24, color: 'var(--accent)' }} />
          <span className="text-[18px] font-semibold tracking-[-0.03em] text-[var(--text)]">Fuse</span>
        </Link>
        <Link
          to={backHref}
          className="ml-auto inline-flex items-center gap-1.5 text-[13.5px] text-[var(--text-mute)] transition-colors hover:text-[var(--text)]"
        >
          <ArrowLeft className="h-[14px] w-[14px]" strokeWidth={1.9} />
          {backLabel}
        </Link>
      </header>

      {/* Center column */}
      <main className="relative z-10 flex flex-1 items-center justify-center px-6 pb-[72px] pt-8">
        <div className="w-full max-w-[392px]">{children}</div>
      </main>
    </div>
  )
}

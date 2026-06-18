import Link from 'next/link'
import { ChevronDown } from 'lucide-react'
import { EXTERNAL_LINKS } from '@/shared/constants/routes'
import { NAV_LINKS } from '../data/site'
import { FuseMark } from './FuseMark'

/**
 * Sticky top nav. Backdrop-blurred translucent background, brand mark
 * with a soft glow, link cluster on the right ending in Log in + a
 * pill-shaped Sign up CTA. Matches `Fuse Site.dc.html` lines 29-48.
 */
export function MarketingNav() {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-xl supports-[backdrop-filter]:bg-background/65">
      <nav className="mx-auto flex h-16 max-w-[1280px] items-center gap-8 px-7">
        <Link href="/" className="flex shrink-0 items-center gap-[9px]">
          <FuseMark className="h-[28px] w-[28px] text-primary" />
          <span className="text-[19px] font-semibold tracking-[-0.03em] text-foreground">
            Fuse
          </span>
        </Link>

        <div className="ml-auto hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="group inline-flex items-center gap-1 rounded-md px-3 py-2 text-[15px] font-medium text-foreground/90 transition-colors hover:text-foreground"
            >
              {item.label}
              {item.hasMenu && (
                <ChevronDown
                  className="h-[14px] w-[14px] text-foreground/55 transition-transform group-hover:translate-y-px"
                  strokeWidth={2}
                />
              )}
            </Link>
          ))}
        </div>

        <div className="flex shrink-0 items-center">
          <Link
            href={EXTERNAL_LINKS.PRODUCT}
            className="inline-flex items-center rounded-md bg-foreground px-3.5 py-1.5 text-[13.5px] font-medium text-background transition-[filter] hover:brightness-110"
          >
            Go to app
          </Link>
        </div>
      </nav>
    </header>
  )
}

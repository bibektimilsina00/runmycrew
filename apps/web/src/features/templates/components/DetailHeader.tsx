import { ArrowLeft, Link2, MoreHorizontal, Download, FileDown, Sparkles } from 'lucide-react'
import { Button, useToast } from '@/shared/components'
import {
  DropdownMenuRoot,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { Tooltip } from '@/shared/components'
import type { TemplateDetail } from '../types/templatesTypes'

/**
 * Sticky sub-header for the detail page — back arrow, icon tile, title,
 * primary action + share/more on the right.
 *
 * `bg-[var(--bg-2)]/95 + backdrop-blur` keeps the header readable when
 * the user scrolls the hero gradient under it. z-30 stays below modals
 * but above the page body.
 */

interface DetailHeaderProps {
  template: TemplateDetail
  onBack: () => void
  onPrimary: () => void
  primaryDisabled?: boolean
  primaryLoading?: boolean
  isOwner: boolean
}

export function DetailHeader({
  template,
  onBack,
  onPrimary,
  primaryDisabled,
  primaryLoading,
  isOwner,
}: DetailHeaderProps) {
  const { toast } = useToast()
  const isPremium = template.is_premium && !isOwner
  const primaryLabel = isPremium ? `Buy for ${formatPrice(template.price_cents)}` : 'Use template'

  const copyLink = () => {
    void navigator.clipboard.writeText(window.location.href)
    toast('Link copied', { variant: 'ok' })
  }

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(template.graph, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${template.slug}.workflow.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="sticky top-0 z-30 border-b border-[var(--border-faint)] bg-[var(--bg-2)]/95 backdrop-blur supports-[backdrop-filter]:bg-[var(--bg-2)]/80">
      <div className="max-w-[1160px] mx-auto px-[28px] sm:px-[48px] py-[14px] flex items-center gap-3">
        <button
          onClick={onBack}
          className="flex h-8 w-8 items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
          title="Back to marketplace"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>

        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] text-white text-[13px] font-bold ${template.bg_variant}`}
          aria-hidden
        >
          {template.title.charAt(0).toUpperCase()}
        </div>

        <span className="truncate text-[15px] font-semibold tracking-[-0.011em] text-[var(--text)]">
          {template.title}
        </span>

        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={onPrimary}
            disabled={primaryDisabled}
            loading={primaryLoading}
            leftIcon={
              isPremium ? <Sparkles className="h-3.5 w-3.5" /> : <Download className="h-3.5 w-3.5" />
            }
            className="font-semibold"
          >
            {primaryLoading ? '…' : primaryLabel}
          </Button>

          <Tooltip content="Copy link">
            <button
              onClick={copyLink}
              className="flex h-8 w-8 items-center justify-center rounded-[7px] border border-[var(--border-faint)] bg-[var(--bg)] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
              aria-label="Copy link"
            >
              <Link2 className="h-3.5 w-3.5" />
            </button>
          </Tooltip>

          <DropdownMenuRoot>
            <DropdownMenuTrigger asChild>
              <button
                className="flex h-8 w-8 items-center justify-center rounded-[7px] border border-[var(--border-faint)] bg-[var(--bg)] text-[var(--text-mute)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
                aria-label="More"
              >
                <MoreHorizontal className="h-3.5 w-3.5" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuItem onClick={exportJson}>
                <FileDown className="h-3.5 w-3.5" /> Export workflow JSON
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenuRoot>
        </div>
      </div>
    </div>
  )
}

function formatPrice(cents: number): string {
  if (cents <= 0) return 'Free'
  const dollars = cents / 100
  return Number.isInteger(dollars) ? `$${dollars}` : `$${dollars.toFixed(2)}`
}

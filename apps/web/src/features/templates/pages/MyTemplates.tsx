import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Icons } from '@/shared/components/icons'
import { Button } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useMyTemplates, useDeleteTemplate } from '../hooks/useTemplates'
import { TemplateCard } from '../components/TemplateCard'
import { useToast } from '@/shared/components'
import type { TemplateListItem } from '../types/templatesTypes'

/**
 * `/templates/mine` — the caller's published templates (drafts + live).
 * Same card grid as the marketplace page; an inline ⋯ menu lets the
 * creator unpublish or delete each one.
 */

export function MyTemplates() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const { data: items = [], isLoading } = useMyTemplates()
  const deleteMutation = useDeleteTemplate()

  const handleDelete = (id: string, title: string) => {
    if (!confirm(`Delete template "${title}"? Existing installs are unaffected.`)) {
      return
    }
    deleteMutation.mutate(id, {
      onSuccess: () => toast('Template deleted', { variant: 'ok' }),
      onError: () => toast('Failed to delete template', { variant: 'err' }),
    })
  }

  return (
    <div className="view-body">
      <button
        onClick={() => navigate(APP_ROUTES.TEMPLATES)}
        className="mb-5 inline-flex items-center gap-1.5 text-[12px] font-medium text-[var(--text-faint)] transition-colors hover:text-[var(--text)]"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to marketplace
      </button>

      <div className="page-head">
        <div>
          <span className="eyebrow">{items.length} template(s)</span>
          <h1>My templates</h1>
        </div>
        <div className="btn-group">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate(APP_ROUTES.AUTOMATIONS)}
            leftIcon={<Icons.Plus />}
          >
            Publish from workflow
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-3 py-8 text-[13px] text-[var(--text-faint)]">
          <div className="w-4 h-4 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
          Loading…
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-1.5 py-16 text-center text-[var(--text-faint)]">
          <span className="text-[13.5px] font-semibold text-[var(--text)]">
            You haven't published any templates yet
          </span>
          <span className="text-[12px]">
            Open a workflow and click "Publish as template" in the topbar.
          </span>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <div key={item.id} className="relative">
              <TemplateCard
                template={item}
                onClick={() => navigate(APP_ROUTES.TEMPLATE_DETAIL(item.slug))}
              />
              {/* Creator-only delete affordance, floating on the card so
                  it's discoverable without an extra row. */}
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDelete(item.id, item.title)
                }}
                className="absolute right-2 top-2 z-20 rounded-[6px] border border-[var(--border-faint)] bg-[var(--bg-2)]/80 px-2 py-1 text-[10.5px] font-semibold text-[var(--err)] backdrop-blur-sm transition-colors hover:bg-[var(--err)]/10"
                title="Delete template"
              >
                Delete
              </button>
              {!item.is_published && (
                <span className="absolute left-2 top-2 z-20 rounded-[5px] border border-[var(--border-faint)] bg-[var(--bg-2)]/90 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.06em] text-[var(--text-faint)]">
                  Draft
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Helper export — Templates page imports the same TemplateListItem.
export type { TemplateListItem }

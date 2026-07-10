import { useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { Button, useToast } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useCredentials } from '@/features/connections/hooks/useConnections'
import { useTemplateDetail, useInstallTemplate } from '../hooks/useTemplates'
import { templatesAPI } from '../services/templatesAPI'
import { DetailHeader } from '../components/DetailHeader'
import { DetailHero } from '../components/DetailHero'
import { DetailSidebar } from '../components/DetailSidebar'
import { DetailTabs } from '../components/DetailTabs'
import { RelatedTemplates } from '../components/RelatedTemplates'

/**
 * Vercel-marketplace-style detail page. Sticky sub-header pinned at the
 * top, big hero preview, two-column body with shadcn Tabs in the main
 * column and a structured info sidebar. Typography + tokens match the
 * dashboard so the page reads as part of the product.
 */
export function TemplateDetail() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const { toast } = useToast()
  const { data: template, isLoading, error } = useTemplateDetail(slug)
  const install = useInstallTemplate()
  const { data: credentials = [] } = useCredentials()

  const connectedTypes = useMemo(
    () => new Set(credentials.map((c) => c.type)),
    [credentials],
  )
  const missingCredentials = useMemo(() => {
    if (!template) return []
    return (template.credentials_required || []).filter(
      (c) => !connectedTypes.has(c),
    )
  }, [template, connectedTypes])

  // Ownership is decided by the backend `install` endpoint (returns 402
  // when the user can't install a premium template); the UI just routes
  // the button based on `is_premium` and lets the server resolve edge
  // cases. The header treats a 402 as "needs purchase" via the toast
  // below.
  const isOwner = false

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center gap-3 px-[48px] py-12 text-[13px] text-[var(--text-faint)]">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading template…
      </div>
    )
  }

  if (error || !template) {
    return (
      <div className="flex-1 flex flex-col items-start gap-3 px-[48px] py-12">
        <h1 className="text-[22px] font-semibold">Template not found</h1>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => navigate(APP_ROUTES.TEMPLATES)}
        >
          Back to marketplace
        </Button>
      </div>
    )
  }

  const handlePrimary = () => {
    if (template.is_premium && !isOwner) {
      void templatesAPI.purchase(template.slug).catch(() => {})
      toast('Template purchases are coming soon', { variant: 'warn' })
      return
    }
    install.mutate(template.slug, {
      onSuccess: (res) => {
        toast(`Installed '${template.title}'`, { variant: 'ok' })
        navigate(APP_ROUTES.WORKFLOW(res.workflow_id))
      },
      onError: (err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status
        if (status === 402) {
          toast('Premium template — purchases coming soon', { variant: 'warn' })
        } else {
          toast('Install failed', { variant: 'err' })
        }
      },
    })
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <DetailHeader
        template={template}
        onBack={() => navigate(APP_ROUTES.TEMPLATES)}
        onPrimary={handlePrimary}
        primaryDisabled={install.isPending}
        primaryLoading={install.isPending}
        isOwner={isOwner}
      />

      <div className="max-w-[1160px] mx-auto px-[28px] sm:px-[48px] pt-[32px] pb-[80px] flex flex-col gap-[32px]">
        <DetailHero template={template} />

        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)] gap-[28px] items-start">
          <DetailTabs template={template} missingCredentials={missingCredentials} />
          <DetailSidebar
            template={template}
            missingCredentials={missingCredentials}
            onInstall={handlePrimary}
            installing={install.isPending}
          />
        </div>

        <RelatedTemplates category={template.category} excludeId={template.id} />
      </div>
    </div>
  )
}

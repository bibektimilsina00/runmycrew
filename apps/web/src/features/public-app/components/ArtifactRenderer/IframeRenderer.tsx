import type { RendererProps } from './types'

/**
 * Direct iframe (as authored by the emitting node). Same sandbox rules
 * as UrlPreview but no header chrome — meant for "canvas embed" cases
 * where the artifact IS the pane.
 */
export function IframeRenderer({ artifact }: RendererProps) {
  const url = String(artifact.data?.url ?? '')
  if (!url) return <div className="p-6 text-[13px] text-white/50">No iframe URL</div>
  const sandbox = String(artifact.data?.sandbox ?? 'allow-scripts')
  return (
    <iframe
      title={artifact.title || url}
      src={url}
      sandbox={sandbox}
      className="h-full w-full border-0 bg-white"
      referrerPolicy="no-referrer"
      loading="lazy"
    />
  )
}

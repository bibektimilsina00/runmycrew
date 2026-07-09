import { useMemo } from 'react'
import type { RendererProps } from './types'

/**
 * Renders raw HTML inside a sandboxed same-origin blob iframe so the
 * emitted markup can't touch the parent document, cookies, or
 * localStorage.
 */
export function HtmlRenderer({ artifact }: RendererProps) {
  const html = String(artifact.data?.html ?? '')
  const src = useMemo(() => {
    if (!html) return ''
    const blob = new Blob([html], { type: 'text/html' })
    return URL.createObjectURL(blob)
  }, [html])
  if (!html) return <div className="p-6 text-[13px] text-white/50">Empty HTML</div>
  return (
    <iframe
      title={artifact.title || 'HTML preview'}
      src={src}
      sandbox="allow-scripts allow-forms"
      className="h-full w-full border-0 bg-white"
      referrerPolicy="no-referrer"
    />
  )
}

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { RendererProps } from './types'

/**
 * GFM markdown with tight typographic defaults. Headings, tables, task
 * lists, fenced code. Code blocks handed to CodeRenderer inline.
 */
export function MarkdownRenderer({ artifact }: RendererProps) {
  const content = String(artifact.data?.content ?? '')
  return (
    <div className="prose prose-invert max-w-none px-6 py-5 text-[14.5px] leading-[1.65]">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}

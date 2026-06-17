import { useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-jsx'
import 'prismjs/components/prism-tsx'
import 'prismjs/components/prism-yaml'
import { Copy, Check } from 'lucide-react'
import { cn } from '@/lib/cn'

interface Props {
  content: string
}

/**
 * Rich-text renderer for Copilot assistant messages.
 *
 * Uses `react-markdown` + `remark-gfm` so responses get proper headings,
 * lists, tables, blockquotes, links, and fenced code blocks. Code blocks
 * are rendered through `<CodeBlock>` which colors tokens with Prism and
 * exposes a Copy button on hover.
 */
export function CopilotMessage({ content }: Props) {
  return (
    <div className="copilot-md max-w-none break-words text-[13.5px] leading-[1.6] text-[var(--text)]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="mb-2.5 mt-5 text-[14px] font-semibold text-[var(--text)] first:mt-0">{children}</h1>,
          h2: ({ children }) => <h2 className="mb-2.5 mt-5 text-[14px] font-semibold text-[var(--text)] first:mt-0">{children}</h2>,
          h3: ({ children }) => <h3 className="mb-2 mt-4 text-[13.5px] font-semibold text-[var(--text)] first:mt-0">{children}</h3>,
          p:  ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="mb-4 ml-5 list-disc space-y-2 marker:text-[var(--text-faint)] last:mb-0">{children}</ul>,
          ol: ({ children }) => <ol className="mb-4 ml-5 list-decimal space-y-2 marker:text-[var(--text-faint)] last:mb-0">{children}</ol>,
          li: ({ children }) => <li className="pl-1 leading-[1.6]">{children}</li>,
          a:  ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] underline-offset-2 hover:underline">
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="mb-3 border-l-2 border-[var(--accent)] bg-[var(--accent-soft)] py-1.5 pl-3 pr-2 text-[var(--text-mute)] last:mb-0">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-3 border-[var(--border-faint)]" />,
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto rounded-[6px] border border-[var(--border-faint)]">
              <table className="min-w-full border-collapse text-[12.5px]">{children}</table>
            </div>
          ),
          th:  ({ children }) => <th className="border-b border-[var(--border-faint)] bg-[var(--surface-2)] px-2 py-1 text-left font-medium text-[var(--text)]">{children}</th>,
          td:  ({ children }) => <td className="border-b border-[var(--border-faint)] px-2 py-1 align-top text-[var(--text-mute)]">{children}</td>,
          strong: ({ children }) => <strong className="font-semibold text-[var(--text)]">{children}</strong>,
          em:     ({ children }) => <em className="italic">{children}</em>,
          code:   InlineOrBlockCode,
          pre:    ({ children }) => <>{children}</>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

// ── Code rendering ────────────────────────────────────────────────────────────

interface CodeProps {
  inline?: boolean
  className?: string
  children?: React.ReactNode
}

function InlineOrBlockCode({ inline, className, children }: CodeProps) {
  const text = String(children ?? '').replace(/\n$/, '')

  // react-markdown 9+ no longer passes `inline`; detect by absence of language
  // class + lack of newlines as a heuristic.
  const looksInline = inline ?? (!className && !text.includes('\n'))
  if (looksInline) {
    return (
      <code className="rounded-[4px] border border-[var(--border-soft)] bg-[var(--surface-2)] px-[5px] py-[1px] font-mono text-[11.5px] text-[var(--accent)]">
        {children}
      </code>
    )
  }

  const lang = /language-(\w+)/.exec(className ?? '')?.[1]
  return <CodeBlock code={text} lang={lang} />
}

function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const [copied, setCopied] = useState(false)

  const html = useMemo(() => {
    if (lang && Prism.languages[lang]) {
      try { return Prism.highlight(code, Prism.languages[lang], lang) } catch { /* fall through */ }
    }
    return escapeHtml(code)
  }, [code, lang])

  const copy = () => {
    void navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="group relative mb-2 overflow-hidden rounded-[8px] border border-[var(--border-faint)] bg-[var(--bg)] last:mb-0">
      <div className="flex items-center justify-between border-b border-[var(--border-faint)] bg-[var(--surface)] px-2.5 py-1">
        <span className="font-mono text-[10.5px] uppercase tracking-wide text-[var(--text-faint)]">
          {lang ?? 'text'}
        </span>
        <button
          onClick={copy}
          className={cn(
            'flex items-center gap-1 rounded-[4px] px-1.5 py-0.5 text-[10.5px] text-[var(--text-faint)] transition-colors',
            'hover:bg-[var(--surface-2)] hover:text-[var(--text)]',
          )}
          title="Copy code"
        >
          {copied ? <Check className="h-3 w-3 text-[var(--ok)]" /> : <Copy className="h-3 w-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="overflow-x-auto px-3 py-2 text-[11.5px] leading-relaxed">
        <code
          className="copilot-md-code font-mono"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </pre>
    </div>
  )
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

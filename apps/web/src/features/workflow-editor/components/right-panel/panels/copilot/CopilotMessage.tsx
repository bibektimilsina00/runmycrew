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
 * Layout matches the Linear-style Copilot panel in Fuse.dc.html:
 *  - body text is 13px / line-height 1.55 / --text-body (#c7c9ce on dark)
 *  - <strong> lifts to --text (#edeef0)
 *  - inline code is --accent-tinted on a faint chip
 *  - fenced code blocks are 9px-radius, JetBrains Mono 11.5px
 *  - ```diff fences get per-line tinting (added = --ok, removed = --err,
 *    context = --text-mute) with a coloured left rule — the exact pattern
 *    used by the design's 'I'll add a Filter step' assistant reply.
 */
export function CopilotMessage({ content }: Props) {
  return (
    <div className="copilot-md max-w-none break-words text-[13px] leading-[1.55] text-[var(--text-body)]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="mb-[10px] mt-[18px] text-[14px] font-semibold text-[var(--text)] first:mt-0">{children}</h1>,
          h2: ({ children }) => <h2 className="mb-[10px] mt-[18px] text-[14px] font-semibold text-[var(--text)] first:mt-0">{children}</h2>,
          h3: ({ children }) => <h3 className="mb-[8px] mt-[14px] text-[13.5px] font-semibold text-[var(--text)] first:mt-0">{children}</h3>,
          p:  ({ children }) => <p className="mb-[10px] last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="mb-[10px] ml-[18px] list-disc space-y-[5px] marker:text-[var(--text-faint)] last:mb-0">{children}</ul>,
          ol: ({ children }) => <ol className="mb-[10px] ml-[18px] list-decimal space-y-[5px] marker:text-[var(--text-faint)] last:mb-0">{children}</ol>,
          li: ({ children }) => <li className="pl-[2px] leading-[1.55]">{children}</li>,
          a:  ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] underline-offset-2 hover:underline">
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="mb-[10px] border-l-2 border-[var(--accent)] bg-[var(--accent-soft)] py-[6px] pl-[12px] pr-[10px] text-[var(--text-mute)] last:mb-0">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-[14px] border-[var(--border-faint)]" />,
          table: ({ children }) => (
            <div className="my-[10px] overflow-x-auto rounded-[7px] border border-[var(--border-soft)]">
              <table className="min-w-full border-collapse text-[12.5px]">{children}</table>
            </div>
          ),
          th: ({ children }) => <th className="border-b border-[var(--border-soft)] bg-[var(--surface-2)] px-[10px] py-[6px] text-left font-medium text-[var(--text)]">{children}</th>,
          td: ({ children }) => <td className="border-b border-[var(--border-faint)] px-[10px] py-[6px] align-top text-[var(--text-mute)]">{children}</td>,
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
  if (lang === 'diff') return <DiffBlock code={text} />
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
    <div className="group relative mb-[10px] overflow-hidden rounded-[9px] border border-[var(--border-soft)] bg-[var(--surface)] last:mb-0">
      <div className="flex items-center justify-between border-b border-[var(--border-faint)] bg-[var(--surface-2)] px-[10px] py-[5px]">
        <span className="font-mono text-[10.5px] uppercase tracking-[0.06em] text-[var(--text-faint)]">
          {lang ?? 'text'}
        </span>
        <button
          onClick={copy}
          className={cn(
            'inline-flex items-center gap-[5px] rounded-[5px] px-[6px] py-[2px] text-[10.5px] text-[var(--text-faint)] transition-colors',
            'hover:bg-[var(--surface-3)] hover:text-[var(--text)]',
          )}
          title="Copy code"
        >
          {copied ? <Check className="h-3 w-3 text-[var(--ok)]" /> : <Copy className="h-3 w-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="overflow-x-auto px-[11px] py-[8px] text-[11.5px] leading-[1.55]">
        <code
          className="copilot-md-code font-mono"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </pre>
    </div>
  )
}

/**
 * ```diff fenced block — per-line render with green/red/muted tints matching
 * the assistant-reply pattern in Fuse.dc.html (e.g. "I'll add a Filter step…"
 * followed by + new line + context line).
 */
function DiffBlock({ code }: { code: string }) {
  const lines = code.split('\n')

  const lineStyle = (line: string): { bg: string; color: string; rule: string | null } => {
    if (line.startsWith('+++') || line.startsWith('---')) {
      return { bg: 'transparent', color: 'var(--text-faint)', rule: null }
    }
    if (line.startsWith('+')) {
      return { bg: 'rgba(76,195,138,0.09)', color: 'var(--ok)', rule: 'var(--ok)' }
    }
    if (line.startsWith('-')) {
      return { bg: 'rgba(229,103,95,0.09)', color: 'var(--err)', rule: 'var(--err)' }
    }
    return { bg: 'rgba(255,255,255,0.02)', color: 'var(--text-mute)', rule: null }
  }

  return (
    <div className="mb-[10px] overflow-hidden rounded-[9px] border border-[var(--border-soft)] font-mono text-[11.5px] leading-[1.55] last:mb-0">
      {lines.map((line, i) => {
        const { bg, color, rule } = lineStyle(line)
        return (
          <div
            key={i}
            className="px-[11px] py-[6px] whitespace-pre"
            style={{
              background: bg,
              color,
              borderLeft: rule ? `2px solid ${rule}` : '2px solid transparent',
            }}
          >
            {line.length === 0 ? ' ' : line}
          </div>
        )
      })}
    </div>
  )
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

'use client'

import { useRef, useState, type ReactNode } from 'react'
import { Check, Copy } from 'lucide-react'

/**
 * Wraps the `<pre>` that rehype-pretty-code emits and adds a copy button.
 * The highlighted markup (spans with inline colors) is passed through
 * untouched; we only read `.textContent` off the rendered node to copy.
 */
export function CodeBlock({ children, ...props }: { children?: ReactNode }) {
  const ref = useRef<HTMLPreElement>(null)
  const [copied, setCopied] = useState(false)

  const copy = () => {
    const text = ref.current?.textContent ?? ''
    void navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    })
  }

  return (
    <div className="group relative my-5">
      <button
        type="button"
        onClick={copy}
        aria-label="Copy code"
        className="absolute right-2.5 top-2.5 z-10 inline-flex h-7 w-7 items-center justify-center rounded-[7px] border border-border bg-background/70 text-muted-foreground opacity-0 backdrop-blur transition-all hover:text-foreground group-hover:opacity-100"
      >
        {copied ? <Check className="h-3.5 w-3.5 text-primary" /> : <Copy className="h-3.5 w-3.5" />}
      </button>
      <pre ref={ref} {...props}>
        {children}
      </pre>
    </div>
  )
}

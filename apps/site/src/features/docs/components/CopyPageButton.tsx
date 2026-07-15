'use client'

import { useState } from 'react'
import { Check, Copy } from 'lucide-react'

/**
 * "Copy page" — grabs the rendered article text so it can be pasted into an
 * LLM or notes. Reads `.prose-docs` innerText at click time; no need to ship
 * the raw markdown down with every page.
 */
export function CopyPageButton() {
  const [copied, setCopied] = useState(false)

  const copy = () => {
    const text = document.querySelector('.prose-docs')
    if (!(text instanceof HTMLElement)) return
    void navigator.clipboard.writeText(text.innerText).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    })
  }

  return (
    <button
      type="button"
      onClick={copy}
      className="inline-flex shrink-0 items-center gap-1.5 rounded-[8px] border border-border px-2.5 py-1.5 text-[12.5px] font-medium text-muted-foreground transition-colors hover:bg-white/[0.04] hover:text-foreground"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-primary" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? 'Copied' : 'Copy page'}
    </button>
  )
}

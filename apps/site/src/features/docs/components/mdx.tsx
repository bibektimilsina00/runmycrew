import Link from 'next/link'
import type { ComponentPropsWithoutRef, ReactNode } from 'react'
import { Info, Lightbulb, AlertTriangle, ArrowUpRight } from 'lucide-react'
import type { MDXComponents } from 'mdx/types'
import { CodeBlock } from './CodeBlock'

/* ── Authoring components usable inside any .mdx page ──────────────────── */

const CALLOUT = {
  note: { icon: Info, cls: 'border-primary/30 bg-primary/[0.06] text-primary' },
  tip: { icon: Lightbulb, cls: 'border-[var(--ok)]/30 bg-[var(--ok)]/[0.06] text-[var(--ok)]' },
  warning: { icon: AlertTriangle, cls: 'border-amber-500/30 bg-amber-500/[0.07] text-amber-400' },
} as const

export function Callout({
  type = 'note',
  title,
  children,
}: {
  type?: keyof typeof CALLOUT
  title?: string
  children: ReactNode
}) {
  const { icon: Icon, cls } = CALLOUT[type] ?? CALLOUT.note
  return (
    <div className={`my-5 flex gap-3 rounded-[10px] border px-4 py-3 ${cls}`}>
      <Icon className="mt-0.5 h-[16px] w-[16px] shrink-0" />
      <div className="min-w-0 text-[14px] leading-[1.6] text-foreground/90 [&>p]:m-0 [&>p+p]:mt-2">
        {title && <div className="mb-1 font-semibold text-foreground">{title}</div>}
        {children}
      </div>
    </div>
  )
}

export function CardGrid({ children }: { children: ReactNode }) {
  return <div className="my-6 grid grid-cols-1 gap-3 sm:grid-cols-2">{children}</div>
}

export function Card({
  title,
  href,
  children,
}: {
  title: string
  href?: string
  children?: ReactNode
}) {
  const inner = (
    <>
      <div className="flex items-center gap-1.5 text-[14.5px] font-semibold text-foreground">
        {title}
        {href && <ArrowUpRight className="h-[15px] w-[15px] text-muted-foreground transition-colors group-hover:text-primary" />}
      </div>
      {children && <div className="mt-1 text-[13.5px] leading-[1.55] text-muted-foreground">{children}</div>}
    </>
  )
  const cls =
    'group block rounded-[12px] border border-border bg-card/30 px-4 py-3.5 no-underline transition-colors hover:border-primary/40 hover:bg-card/60'
  return href ? (
    <Link href={href} className={cls}>
      {inner}
    </Link>
  ) : (
    <div className={cls}>{inner}</div>
  )
}

export function Steps({ children }: { children: ReactNode }) {
  return (
    <div className="my-6 flex flex-col gap-0 border-l border-border pl-6 [counter-reset:step] [&>*]:relative">
      {children}
    </div>
  )
}

export function Step({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="pb-6 [counter-increment:step] last:pb-0">
      <span className="absolute -left-[33px] flex h-[22px] w-[22px] items-center justify-center rounded-full border border-border bg-background text-[11px] font-semibold text-foreground before:content-[counter(step)]" />
      <div className="mb-1 text-[15px] font-semibold text-foreground">{title}</div>
      <div className="text-[14.5px] leading-[1.65] text-muted-foreground [&>p]:m-0 [&>p+*]:mt-2">
        {children}
      </div>
    </div>
  )
}

/* ── Base HTML element overrides for GitHub-flavored markdown ──────────── */

function anchor(id?: string) {
  return id ? (
    <a href={`#${id}`} className="doc-anchor" aria-label="Link to this section">
      #
    </a>
  ) : null
}

export const mdxComponents: MDXComponents = {
  h1: (p) => <h1 {...p} />,
  h2: ({ id, children, ...p }: ComponentPropsWithoutRef<'h2'>) => (
    <h2 id={id} className="group scroll-mt-24" {...p}>
      {children}
      {anchor(id)}
    </h2>
  ),
  h3: ({ id, children, ...p }: ComponentPropsWithoutRef<'h3'>) => (
    <h3 id={id} className="group scroll-mt-24" {...p}>
      {children}
      {anchor(id)}
    </h3>
  ),
  a: ({ href = '', children, ...p }: ComponentPropsWithoutRef<'a'>) => {
    const external = /^https?:\/\//.test(href)
    if (external)
      return (
        <a href={href} target="_blank" rel="noopener noreferrer" {...p}>
          {children}
        </a>
      )
    return (
      <Link href={href} {...p}>
        {children}
      </Link>
    )
  },
  pre: CodeBlock,
  table: (p) => (
    <div className="my-6 overflow-x-auto rounded-[10px] border border-border">
      <table className="w-full border-collapse text-[13.5px]" {...p} />
    </div>
  ),
  Callout,
  Card,
  CardGrid,
  Steps,
  Step,
}

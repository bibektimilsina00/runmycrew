'use client'

import { useState } from 'react'
import { Loader2, Check } from 'lucide-react'

/**
 * Working "Contact sales" form. There is no server mailer wired into the
 * marketing site, so on submit it composes a fully pre-filled email to the
 * sales inbox and hands off to the visitor's mail client — zero backend,
 * always works. Swap `openMail` for a POST to a `/api/contact` route once
 * an email provider (Resend) is wired in.
 */
export function ContactForm() {
  const [sent, setSent] = useState(false)
  const [sending, setSending] = useState(false)

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    const name = String(f.get('name') ?? '').trim()
    const email = String(f.get('email') ?? '').trim()
    const company = String(f.get('company') ?? '').trim()
    const message = String(f.get('message') ?? '').trim()

    const subject = `Sales enquiry — ${name || 'RunMyCrew'}`
    const lines = [`Name: ${name}`, `Email: ${email}`]
    if (company) lines.push(`Company: ${company}`)
    lines.push('', message)
    const body = lines.join('\n')

    setSending(true)
    window.location.href = `mailto:support@runmycrew.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
    // Give the mail client a beat to take over, then show confirmation.
    window.setTimeout(() => {
      setSending(false)
      setSent(true)
    }, 600)
  }

  if (sent) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-card/40 px-6 py-10 text-center">
        <span className="grid h-10 w-10 place-items-center rounded-full bg-primary/15 text-primary">
          <Check className="h-5 w-5" strokeWidth={2.4} />
        </span>
        <h2 className="m-0 text-[17px] font-semibold tracking-tight text-foreground">Your email is ready to send</h2>
        <p className="m-0 max-w-[420px] text-[14px] text-muted-foreground">
          We opened your mail client with the details pre-filled. Prefer another way? Reach us directly at{' '}
          <a href="mailto:support@runmycrew.com" className="text-primary">support@runmycrew.com</a>.
        </p>
        <button
          onClick={() => setSent(false)}
          className="mt-1 text-[13px] font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          Send another
        </button>
      </div>
    )
  }

  return (
    <form onSubmit={onSubmit} className="rounded-xl border border-border bg-card/40 p-6">
      <h2 className="m-0 text-[17px] font-semibold tracking-tight text-foreground">Talk to us</h2>
      <p className="mt-1 text-[14px] text-muted-foreground">
        Tell us what you&apos;re building — we&apos;ll get back within one business day.
      </p>

      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Name" name="name" placeholder="Ada Lovelace" required />
        <Field label="Work email" name="email" type="email" placeholder="ada@company.com" required />
      </div>
      <div className="mt-4">
        <Field label="Company" name="company" placeholder="Acme Inc. (optional)" />
      </div>
      <div className="mt-4 flex flex-col gap-2">
        <label htmlFor="message" className="text-[13px] font-medium text-foreground/90">
          How can we help?
        </label>
        <textarea
          id="message"
          name="message"
          required
          rows={4}
          placeholder="We want to automate our support triage across GitHub, Slack and Notion…"
          className="w-full resize-none rounded-lg border border-border bg-background/60 px-3 py-2.5 text-[14px] text-foreground outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-primary/60"
        />
      </div>

      <button
        type="submit"
        disabled={sending}
        className="mt-5 inline-flex h-[38px] items-center gap-2 rounded-[8px] bg-primary px-5 text-[13px] font-semibold text-primary-foreground transition-[filter] hover:brightness-110 disabled:opacity-70"
      >
        {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
        {sending ? 'Opening…' : 'Send message'}
      </button>
    </form>
  )
}

function Field({
  label,
  name,
  type = 'text',
  placeholder,
  required,
}: {
  label: string
  name: string
  type?: string
  placeholder?: string
  required?: boolean
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={name} className="text-[13px] font-medium text-foreground/90">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        required={required}
        placeholder={placeholder}
        className="h-[38px] w-full rounded-lg border border-border bg-background/60 px-3 text-[14px] text-foreground outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-primary/60"
      />
    </div>
  )
}

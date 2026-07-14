import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter, ContactForm } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Contact',
  description:
    'How to reach RunMyCrew — support, security, privacy, partnerships.',
}

type Channel = {
  title: string
  email: string
  detail: string
  sla: string
}

const CHANNELS: Channel[] = [
  {
    title: 'Customer support',
    email: 'support@runmycrew.com',
    detail:
      'Account, billing, integration setup, bug reports, feature requests.',
    sla: '< 1 business day (free tier), < 4 hours (pro), < 1 hour (enterprise)',
  },
  {
    title: 'Privacy / GDPR',
    email: 'privacy@runmycrew.com',
    detail:
      'Data-subject access, deletion, portability, processing objections.',
    sla: 'Acknowledged in 3 business days; resolved within 30 days',
  },
  {
    title: 'Security',
    email: 'security@runmycrew.com',
    detail:
      'Vulnerability reports, security questionnaires, incident escalation.',
    sla: 'Acknowledged within 24 hours',
  },
  {
    title: 'Legal',
    email: 'legal@runmycrew.com',
    detail:
      'DMCA, subpoenas, court orders, MSA / DPA negotiation.',
    sla: 'Acknowledged within 3 business days',
  },
  {
    title: 'Partnerships & integrations',
    email: 'partners@runmycrew.com',
    detail:
      'New integration proposals, design-partner programs, co-marketing.',
    sla: 'Replied to within 5 business days',
  },
]

export default function ContactPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Company · Contact
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Contact
            </h1>
            <p className="mt-4 text-[15px] text-muted-foreground">
              Pick the inbox that matches what you need — every channel goes
              to a real human and has a documented SLA.
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <div className="mb-10">
              <ContactForm />
            </div>

            <p className="m-0 mb-4 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Or reach a specific team
            </p>
            <div className="flex flex-col gap-4">
              {CHANNELS.map((c) => (
                <a
                  key={c.email}
                  href={`mailto:${c.email}`}
                  className="block rounded-xl border border-border bg-card/50 p-5 transition-colors hover:border-foreground/30 hover:bg-card"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className="m-0 text-[17px] font-semibold tracking-tight text-foreground">
                      {c.title}
                    </h2>
                    <span className="font-mono text-[13px] text-primary">
                      {c.email}
                    </span>
                  </div>
                  <p className="mt-2 text-[14px] text-muted-foreground">
                    {c.detail}
                  </p>
                  <p className="mt-2 text-[12.5px] text-muted-foreground/80">
                    <strong>SLA:</strong> {c.sla}
                  </p>
                </a>
              ))}
            </div>

            <div className="mt-12 rounded-xl border border-border bg-card/40 p-6">
              <h2 className="m-0 text-[17px] font-semibold tracking-tight text-foreground">
                Postal address
              </h2>
              <p className="mt-2 text-[14px] text-muted-foreground">
                RunMyCrew (proprietor: Bibek Timilsina)
                <br />
                Kathmandu, Nepal
                <br />
                Full registered address available on request to{' '}
                <a href="mailto:legal@runmycrew.com">legal@runmycrew.com</a>.
              </p>
            </div>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}

import {
  MarketingNav,
  MarketingFooter,
  Hero,
  LogoCloud,
  Statement,
  FeatureSection,
  MockupWorkflow,
  MockupIntegrations,
  MockupRuns,
  MockupObserve,
  Changelog,
  Testimonials,
  FinalCTA,
  FEATURES,
} from '@/features/marketing'

/**
 * Marketing landing route. Thin shell — every visual section is its own
 * feature component. Add new sections by importing from
 * `@/features/marketing` and dropping them in below.
 */
export default function Home() {
  return (
    <>
      <MarketingNav />
      <main>
        <Hero />
        <LogoCloud />
        <Statement />
        <FeatureSection meta={FEATURES.build}   mockup={<MockupWorkflow />} />
        <FeatureSection meta={FEATURES.connect} mockup={<MockupIntegrations />} />
        <FeatureSection meta={FEATURES.run}     mockup={<MockupRuns />} />
        <FeatureSection meta={FEATURES.observe} mockup={<MockupObserve />} />
        <Changelog />
        <Testimonials />
        <FinalCTA />
      </main>
      <MarketingFooter />
    </>
  )
}

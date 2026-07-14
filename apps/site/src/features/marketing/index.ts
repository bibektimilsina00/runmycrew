/**
 * Marketing feature barrel — every consumer outside this folder imports
 * from `@/features/marketing` so the internal file layout stays
 * refactorable. Add new sections by re-exporting them from here.
 */
export { MarketingNav }      from './components/MarketingNav'
export { MarketingFooter }   from './components/MarketingFooter'
export { Hero }              from './components/Hero'
export { LogoCloud }         from './components/LogoCloud'
export { Statement }         from './components/Statement'
export { FeatureSection }    from './components/FeatureSection'
export { MockupWorkflow }    from './components/MockupWorkflow'
export { MockupIntegrations } from './components/MockupIntegrations'
export { MockupRuns }        from './components/MockupRuns'
export { MockupObserve }     from './components/MockupObserve'
export { Changelog }         from './components/Changelog'
export { Testimonials }      from './components/Testimonials'
export { FinalCTA }          from './components/FinalCTA'
export { ContactForm }       from './components/ContactForm'

export { FEATURES } from './data/site'

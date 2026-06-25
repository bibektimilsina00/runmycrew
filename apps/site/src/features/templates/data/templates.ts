/**
 * Shape of a workflow template as the marketing site cares about it.
 * The live list now comes from the API (`fetchPublicTemplates`); this
 * file is kept only for the shared TypeScript types so the card and
 * grid components have a stable contract.
 */

export type TemplateCategory =
  | 'Sales'
  | 'Marketing'
  | 'Engineering'
  | 'Operations'
  | 'Support'
  | 'Internal'

export type TemplateStep = {
  letter: string
  color: string
  label: string
}

export type Template = {
  slug: string
  title: string
  category: TemplateCategory | string
  description: string
  steps: TemplateStep[]
}

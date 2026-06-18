/**
 * Single source of truth for site URLs. Mirrors apps/web's
 * `shared/constants/routes.ts` pattern so links stay refactorable.
 */
export const APP_ROUTES = {
  HOME: '/',
  PRICING: '/pricing',
  DOCS: '/docs',
  CHANGELOG: '/changelog',
  CONTACT: '/contact',
} as const

export const EXTERNAL_LINKS = {
  PRODUCT: 'https://app.fuse.bibektimilsina.tech',
  GITHUB: 'https://github.com/bibektimilsina00/fuse_monorepo',
  LOGIN: 'https://app.fuse.bibektimilsina.tech/login',
  REGISTER: 'https://app.fuse.bibektimilsina.tech/register',
} as const

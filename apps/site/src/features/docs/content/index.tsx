import type { ReactNode } from 'react'
import type { TocEntry } from '../components/DocsToc'
import { GET_STARTED } from './get-started'
import { BUILDING } from './building'
import { CONNECTIONS } from './connections'
import { RUN_OBSERVE } from './run-observe'
import { SELF_HOST } from './self-host'
import { API } from './api'

export type DocContent = { toc: TocEntry[]; body: ReactNode }

/**
 * Rich doc bodies keyed by slug (the same slugs as `DOCS_NAV`). The
 * catch-all route renders `body` + `toc` when a slug is present here, and
 * falls back to a placeholder otherwise. Grouped source files keep each
 * section editable in isolation.
 */
export const DOC_CONTENT: Record<string, DocContent> = {
  ...GET_STARTED,
  ...BUILDING,
  ...CONNECTIONS,
  ...RUN_OBSERVE,
  ...SELF_HOST,
  ...API,
}

import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import matter from 'gray-matter'
import GithubSlugger from 'github-slugger'

/**
 * Filesystem-backed docs source. Every page is an `.mdx` file under
 * `src/content/docs/**`; frontmatter drives the title, description, sidebar
 * group and order. The sidebar tree, TOC, and prev/next pager are all derived
 * from here — there is no hand-maintained nav list to keep in sync.
 *
 * Slug = file path relative to the content root, minus the extension.
 * `index.mdx` maps to the empty slug (the `/docs` root).
 */

export type DocFrontmatter = {
  title: string
  description?: string
  group: string
  order?: number
}

export type DocMeta = {
  slug: string // '', 'quickstart', 'api/auth'
  href: string // '/docs', '/docs/quickstart'
  frontmatter: DocFrontmatter
}

export type TocEntry = { id: string; label: string; depth: 2 | 3 }

export type NavGroup = { group: string; items: DocMeta[] }

const CONTENT_ROOT = path.join(process.cwd(), 'src/content/docs')

// Sidebar group order. Any group not listed here is appended alphabetically
// after these — so adding a page in a new group still shows up, just at the
// bottom until it's slotted in here.
const GROUP_ORDER = [
  'Get started',
  'Building workflows',
  'Connections',
  'Run & observe',
  'Self-hosting',
  'API',
]

function walk(dir: string): string[] {
  const out: string[] = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) out.push(...walk(full))
    else if (entry.name.endsWith('.mdx')) out.push(full)
  }
  return out
}

function slugFromFile(file: string): string {
  const rel = path.relative(CONTENT_ROOT, file).replace(/\.mdx$/, '')
  return rel === 'index' ? '' : rel.replace(/\/index$/, '')
}

/** All docs, read + parsed once per process (module scope caches it). */
let _all: DocMeta[] | null = null
function all(): DocMeta[] {
  if (_all) return _all
  _all = walk(CONTENT_ROOT)
    .map((file) => {
      const { data } = matter(fs.readFileSync(file, 'utf8'))
      const slug = slugFromFile(file)
      return {
        slug,
        href: slug ? `/docs/${slug}` : '/docs',
        frontmatter: data as DocFrontmatter,
      }
    })
    .sort(
      (a, b) =>
        (a.frontmatter.order ?? 999) - (b.frontmatter.order ?? 999) ||
        a.frontmatter.title.localeCompare(b.frontmatter.title),
    )
  return _all
}

/** Grouped, ordered nav tree for the sidebar. */
export function getNav(): NavGroup[] {
  const byGroup = new Map<string, DocMeta[]>()
  for (const doc of all()) {
    const g = doc.frontmatter.group ?? 'Docs'
    if (!byGroup.has(g)) byGroup.set(g, [])
    byGroup.get(g)!.push(doc)
  }
  const rank = (g: string) => {
    const i = GROUP_ORDER.indexOf(g)
    return i === -1 ? GROUP_ORDER.length : i
  }
  return [...byGroup.entries()]
    .sort(([a], [b]) => rank(a) - rank(b) || a.localeCompare(b))
    .map(([group, items]) => ({ group, items }))
}

/** Flat, ordered list — used for prev/next pagination. */
export function getFlatDocs(): DocMeta[] {
  return getNav().flatMap((g) => g.items)
}

export function getAllSlugs(): string[][] {
  return all()
    .filter((d) => d.slug !== '')
    .map((d) => d.slug.split('/'))
}

export type LoadedDoc = {
  meta: DocMeta
  content: string
  toc: TocEntry[]
  prev: DocMeta | null
  next: DocMeta | null
}

/** Load a single doc by slug segments, or null if it doesn't exist. */
export function getDoc(slugSegments: string[]): LoadedDoc | null {
  const slug = slugSegments.join('/')
  const file = path.join(CONTENT_ROOT, slug === '' ? 'index.mdx' : `${slug}.mdx`)
  const nested = path.join(CONTENT_ROOT, slug, 'index.mdx')
  const target = fs.existsSync(file) ? file : fs.existsSync(nested) ? nested : null
  if (!target) return null

  const { data, content } = matter(fs.readFileSync(target, 'utf8'))
  const flat = getFlatDocs()
  const idx = flat.findIndex((d) => d.slug === slug)

  return {
    meta: { slug, href: slug ? `/docs/${slug}` : '/docs', frontmatter: data as DocFrontmatter },
    content,
    toc: extractToc(content),
    prev: idx > 0 ? flat[idx - 1] : null,
    next: idx >= 0 && idx < flat.length - 1 ? flat[idx + 1] : null,
  }
}

// Pull h2/h3 from the raw MDX for the "On this page" rail. Slugs match
// rehype-slug (both use github-slugger), so anchor links line up. Fenced code
// is stripped first so a `## comment` inside a block never becomes a heading.
function extractToc(source: string): TocEntry[] {
  const slugger = new GithubSlugger()
  const body = source.replace(/```[\s\S]*?```/g, '')
  const out: TocEntry[] = []
  for (const line of body.split('\n')) {
    const m = /^(#{2,3})\s+(.+?)\s*$/.exec(line)
    if (!m) continue
    const label = m[2].replace(/[*`_]/g, '').trim()
    out.push({ id: slugger.slug(label), label, depth: m[1].length as 2 | 3 })
  }
  return out
}

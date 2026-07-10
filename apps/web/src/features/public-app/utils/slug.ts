/** Mirror of the backend's `_slugify` in apps/repository.py — the public
 *  app URL is derived, not stored, so both sides must agree. */
export function slugifyAppUrl(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '') || 'app'
}

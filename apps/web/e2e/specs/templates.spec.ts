import { expect, test } from '@playwright/test'

import { API, apiContext, seededToken } from '../api'

/**
 * Templates marketplace: gallery cards render a real MiniGraph preview
 * (SVG bezier edges + icon-chip spans laid out from the graph), the
 * detail page exposes a "Use template" button, and installing lands in
 * the workflow editor with the template's nodes on the canvas.
 */

interface TemplateItem {
  slug: string
  title: string
  is_premium: boolean
  graph?: { nodes?: unknown[]; edges?: unknown[] }
}

async function fetchTemplates(): Promise<TemplateItem[]> {
  // seededToken avoids /auth calls — they're rate limited to 5/minute.
  const ctx = await apiContext(seededToken())
  const res = await ctx.get(`${API}/templates/?limit=48&offset=0&sort=popular`)
  expect(res.ok(), `templates list failed: ${res.status()}`).toBe(true)
  const body = (await res.json()) as { items: TemplateItem[] }
  return body.items
}

test.describe('templates marketplace', () => {
  test('gallery renders template cards with graph previews', async ({ page }) => {
    const items = await fetchTemplates()
    // The e2e stack seeds official templates on API startup
    // (apps/api/app/features/templates/seeder.py) — the gallery is never
    // empty here. If this throws, the seeder didn't run.
    expect(items.length).toBeGreaterThan(0)

    await page.goto('/templates')
    await expect(
      page.getByRole('heading', { name: 'Templates for every workflow.' }),
    ).toBeVisible()

    // Every list item renders as a card (a <button> wrapping an <h3> title).
    const cards = page.getByRole('button').filter({ has: page.locator('h3') })
    await expect(cards).toHaveCount(items.length)

    // Cards with a non-empty graph render a MiniGraph preview: an
    // aria-hidden SVG (edges) + absolutely positioned icon chips, one
    // span[title=<node type>] per node.
    const withGraph = items.find((t) => (t.graph?.nodes?.length ?? 0) > 0)
    expect(withGraph, 'expected at least one seeded template with a graph').toBeTruthy()
    const card = cards.filter({ hasText: withGraph!.title }).first()
    await expect(card).toBeVisible()
    await expect(card.locator('svg[aria-hidden="true"]').first()).toBeVisible()
    const chips = card.locator('span[title]')
    await expect(chips).toHaveCount(withGraph!.graph!.nodes!.length)
    // Edges draw as <path> elements inside the preview SVG.
    if ((withGraph!.graph!.edges?.length ?? 0) > 0) {
      expect(await card.locator('svg[aria-hidden="true"] path').count()).toBeGreaterThan(0)
    }
  })

  test('detail page → Use template → editor canvas shows nodes', async ({ page }) => {
    const items = await fetchTemplates()
    // Premium templates route to a "purchases coming soon" toast instead
    // of installing — pick a free one with a real graph.
    const target = items.find((t) => !t.is_premium && (t.graph?.nodes?.length ?? 0) > 0)
    expect(target, 'expected a free seeded template with a graph').toBeTruthy()

    await page.goto('/templates')
    await page
      .getByRole('button')
      .filter({ has: page.locator('h3') })
      .filter({ hasText: target!.title })
      .first()
      .click()

    // Detail page: sticky header carries the title + primary action.
    await page.waitForURL(`**/templates/${target!.slug}`)
    await expect(page.getByText(target!.title).first()).toBeVisible()
    const useButton = page.getByRole('button', { name: 'Use template' }).first()
    await expect(useButton).toBeVisible()

    // Install → navigates straight into the created workflow's editor.
    await useButton.click()
    await page.waitForURL(/\/workflows\/[0-9a-f-]{36}/, { timeout: 20_000 })

    // Canvas hydrated the template graph — one .react-flow__node per node.
    const canvasNodes = page.locator('.react-flow__node')
    await expect(canvasNodes.first()).toBeVisible({ timeout: 20_000 })
    await expect(canvasNodes).toHaveCount(target!.graph!.nodes!.length)
  })
})

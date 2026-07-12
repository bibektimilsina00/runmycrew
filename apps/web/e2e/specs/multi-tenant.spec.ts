import { expect, test } from '@playwright/test'

import { API, apiContext, createWorkflow, node, registerAndLogin, seededToken } from '../api'

/**
 * Tenant isolation: a workflow created by user 1 must be invisible to
 * user 2 — both at the API layer (scoped lookup 404s) and in the editor
 * UI (EditorError state, never user 1's graph).
 */

test('another user cannot open or fetch my workflow', async ({ browser }) => {
  test.slow() // registering user 2 may wait out the 5/min auth rate limit
  const uniq = Date.now()

  // User 1 (the seeded default) owns a trivial workflow.
  const token1 = seededToken()
  const wf = await createWorkflow(token1, `E2E Tenant ${uniq}`, {
    nodes: [node('t1', 'trigger.manual', 'Manual', {})],
    edges: [],
  })

  // Sanity: the owner can fetch it (so the negative below is about
  // tenancy, not a bad id).
  const ownerCtx = await apiContext(token1)
  expect((await ownerCtx.get(`${API}/workflows/${wf.id}`)).status()).toBe(200)

  // User 2: fresh account, own personal workspace.
  const token2 = await registerAndLogin(`tenant2-${uniq}@example.com`)

  // API layer: workspace-scoped lookup → 404 (or 403), never 200.
  const ctx2 = await apiContext(token2)
  const res = await ctx2.get(`${API}/workflows/${wf.id}`)
  expect([403, 404]).toContain(res.status())

  // UI layer: log in as user 2 the way the app stores auth
  // (localStorage 'runmycrew-auth-token' — authStore.ts) and open
  // user 1's editor URL directly.
  const context = await browser.newContext({ storageState: { cookies: [], origins: [] } })
  await context.addInitScript((t) => {
    localStorage.setItem('runmycrew-auth-token', t)
  }, token2)
  const page = await context.newPage()
  await page.goto(`/workflows/${wf.id}`)

  // WorkflowEditor renders the EditorError overlay on a load failure.
  await expect(page.getByText('Failed to load workflow')).toBeVisible({ timeout: 20_000 })
  await expect(page.getByRole('button', { name: 'Back to automations' })).toBeVisible()
  // And definitely not user 1's graph.
  await expect(page.locator('.react-flow__node')).toHaveCount(0)

  await context.close()
})

import { expect, test } from '@playwright/test'

import { API, apiContext, edge, node, registerAndLogin } from '../api'

/**
 * Failures must surface with a REAL reason in the public chat, not a
 * bare "No response produced.".
 *
 * Setup trap: the agent node falls back to ANY credential of the
 * provider's type owned by the crew owner (agent.py `_get_api_key`),
 * and globalSetup seeds a mock OpenAI credential for the default e2e
 * user — under that user the agent would succeed against the mock LLM.
 * So the broken crew is owned by a FRESH user with zero credentials.
 */

test('agent without credential surfaces a real error in public chat', async ({ page }) => {
  test.slow() // registering the fresh owner may wait out the 5/min auth rate limit
  const uniq = Date.now()
  const owner = `err-owner-${uniq}@example.com`
  const token = await registerAndLogin(owner)
  const ctx = await apiContext(token)

  // trigger.chat_app → action.agent, provider openai, no credential prop.
  const name = `E2E Err ${uniq}`
  const created = await ctx.post(`${API}/crews/`, {
    data: {
      name,
      graph: {
        nodes: [
          node('trigger1', 'trigger.chat_app', 'Chat App', {}),
          node(
            'agent1',
            'action.agent',
            'Agent',
            { provider: 'openai', messages: [{ role: 'user', content: 'hi' }] },
            { x: 320, y: 0 },
          ),
        ],
        edges: [edge('trigger1', 'agent1')],
      },
    },
  })
  expect(created.ok(), `crew create failed: ${await created.text()}`).toBe(true)
  const crew = (await created.json()) as { id: string }

  // Activate — an active crew with a trigger.chat_app node IS the public app.
  const toggled = await ctx.post(`${API}/crews/${crew.id}/toggle`)
  expect(toggled.ok(), `toggle failed: ${await toggled.text()}`).toBe(true)
  expect(((await toggled.json()) as { is_active: boolean }).is_active).toBe(true)

  // Public URL: /apps/<workspace-slug>/<slugified crew name>.
  const wsRes = await ctx.get(`${API}/workspaces/`)
  expect(wsRes.ok()).toBe(true)
  const workspaces = (await wsRes.json()) as { slug: string }[]
  const appSlug = `e2e-err-${uniq}` // _slugify("E2E Err <uniq>")

  await page.goto(`/apps/${workspaces[0].slug}/${appSlug}`)
  const input = page.getByRole('textbox', { name: 'Message' })
  await expect(input).toBeVisible()
  await expect(input).toBeEnabled()
  await input.fill('hello, who are you?')
  await page.getByRole('button', { name: 'Send message' }).click()

  // The run fails in the worker; the runner wraps the node error as
  // "Node Agent failed: OpenAI API key credential is required." and the
  // stream's execution_failed event flips the bubble to is_error.
  const errorText = page.getByText(/credential is required|failed/i)
  await expect(errorText.first()).toBeVisible({ timeout: 45_000 })
  await expect(page.getByText(/credential/i).first()).toBeVisible()

  // Error styling, not a plain assistant bubble (MessageBubble is_error path).
  await expect(page.locator('[class*="border-red-500"]').first()).toBeVisible()

  // And NOT the reason-less fallback.
  await expect(page.getByText('No response produced.')).toHaveCount(0)
})

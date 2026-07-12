import { expect, test } from '@playwright/test'

import {
  createActiveCrew,
  edge,
  ensureMockCredential,
  node,
  seededToken,
  slugify,
  workspaceSlug,
} from '../api'

/**
 * Hosted chat-app round-trip against the mock LLM:
 * crew(trigger.chat_app → action.agent) served at /apps/<ws>/<slug>.
 *
 * Covers: public page render (welcome headline + input), a full
 * message → SSE stream → "Echo: …" reply, and the conversation
 * sidebar (New chat + switching back to a previous conversation).
 */

// Unique per run — the app slug derives from the trigger title, and a
// stale active crew from a previous run would otherwise win resolution.
const TITLE = `E2E Chat ${Date.now()}`
const SLUG = slugify(TITLE)

let ws: string

test.beforeAll(async () => {
  const token = seededToken()
  const credentialId = await ensureMockCredential(token)
  ws = await workspaceSlug(token)

  await createActiveCrew(token, TITLE, {
    nodes: [
      node('trig', 'trigger.chat_app', 'Chat App', { title: TITLE }),
      node(
        'agent',
        'action.agent',
        'Agent',
        {
          provider: 'openai',
          credential: credentialId,
          messages: [{ role: 'user', content: '{{$step.message}}' }],
        },
        { x: 240, y: 0 },
      ),
    ],
    edges: [edge('trig', 'agent')],
  })
})

test.describe('hosted chat app', () => {
  test('welcome renders, message echoes back, sidebar switches conversations', async ({
    page,
  }) => {
    await page.goto(`/apps/${ws}/${SLUG}`)

    // Welcome state: default headline is `Talk to <title>`.
    await expect(
      page.getByRole('heading', { name: `Talk to ${TITLE}` }),
    ).toBeVisible()

    // Wait for the conversation query to hydrate: useAppendMessage drops
    // optimistic entries while its cache is still empty.
    await page.waitForLoadState('networkidle')

    // Send a message. Placeholder is `Message <title>…` (unicode ellipsis).
    const input = page.getByPlaceholder(`Message ${TITLE}`)
    await input.fill('hello e2e')
    await input.press('Enter')

    // The user bubble appears immediately; the assistant reply lands when
    // the worker finishes (mock LLM echoes the last user message).
    await expect(page.getByText('hello e2e').first()).toBeVisible()
    await expect(page.getByText('Echo: hello e2e')).toBeVisible({
      timeout: 60_000,
    })

    // ── Conversation sidebar ──────────────────────────────────────
    // Two "New chat" buttons exist (header + sidebar); scope to the rail.
    const sidebar = page.locator('aside')
    await sidebar.getByRole('button', { name: 'New chat' }).click()

    // Fresh conversation: transcript resets to the welcome state.
    await expect(
      page.getByRole('heading', { name: `Talk to ${TITLE}` }),
    ).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('Echo: hello e2e')).toBeHidden()

    // The previous conversation shows up in Recents, titled by its first
    // user message. Switching back restores the old transcript.
    const previous = sidebar.getByRole('button', { name: 'hello e2e' })
    await expect(previous).toBeVisible({ timeout: 15_000 })
    await previous.click()
    await expect(page.getByText('Echo: hello e2e')).toBeVisible({
      timeout: 15_000,
    })
  })
})

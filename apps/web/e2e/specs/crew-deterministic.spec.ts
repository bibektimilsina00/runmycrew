import { expect, test } from '@playwright/test'

import { edge, createActiveCrew, node, seededToken, slugify, workspaceSlug } from '../api'

/**
 * Crew maker/checker loop mechanics WITHOUT any LLM — the same
 * form → ai.agent_crew → ai.verify gate graph as the backend contract
 * tests (apps/api/tests/test_crew_loop.py::_gate_graph).
 *
 * amount=120 → verify passes round 1 → crew terminates `success`.
 * amount=900 → verify can never pass → stagnation after round 2 → `stalled`.
 *
 * App-message runs persist no execution row, so the terminal outcome is
 * asserted from the SSE stream the page itself opens: the
 * `execution_completed` frame carries the crew's full output
 * (`{"status": "success"|"stalled", "rounds": …, "result": {"passed": …}}`).
 */

const NAME = `E2E Gate ${Date.now()}`
const SLUG = slugify(NAME)

let ws: string

test.beforeAll(async () => {
  const token = seededToken()
  ws = await workspaceSlug(token)

  await createActiveCrew(token, NAME, {
    nodes: [
      node('form', 'trigger.form', 'Form', {
        inputs: [{ name: 'amount', type: 'number', value: '' }],
      }),
      node(
        'crew',
        'ai.agent_crew',
        'Crew',
        { goal: 'gate', maxRounds: 2, minRounds: 1, stagnationRounds: 1 },
        { x: 240, y: 0 },
      ),
      node(
        'check',
        'ai.verify',
        'Check',
        { mode: 'expression', level: 1, expression: '{{$step.amount}} <= 500' },
        { x: 480, y: 0 },
      ),
    ],
    edges: [edge('form', 'crew'), edge('crew', 'check')],
  })
})

/** Submit the hosted form and return the full SSE body of the run. */
async function submitAmount(
  page: import('@playwright/test').Page,
  amount: number,
): Promise<string> {
  await page.goto(`/apps/${ws}/${SLUG}`)
  await expect(page.getByRole('heading', { name: NAME })).toBeVisible()
  // Wait for the conversation query to hydrate: useAppendMessage drops the
  // optimistic user entry when its cache is still empty (`if (!envelope)
  // return prev`), which loses the transcript on a fast submit.
  await page.waitForLoadState('networkidle')

  await page.locator('#field-amount').fill(String(amount))
  const streamDone = page.waitForResponse((r) => r.url().includes('/stream/'), {
    timeout: 60_000,
  })
  await page.getByRole('button', { name: 'Run' }).click()

  // The submitted values echo into the transcript as the user entry.
  await expect(page.getByText(`amount: ${amount}`)).toBeVisible()

  // SSE closes on the terminal frame; text() resolves with the whole body.
  const body = await (await streamDone).text()

  // The turn completes on the page: the crew's terminal output carries no
  // `content`, so the assistant entry renders the explicit empty state.
  await expect(page.getByText('No response produced.')).toBeVisible({
    timeout: 60_000,
  })
  return body
}

test.describe('crew loop — deterministic gate', () => {
  // Each test gets a fresh browser context (fresh visitor cookie), so the
  // two submissions land in independent app sessions.

  test('amount within the gate → crew succeeds in round 1', async ({ page }) => {
    const sse = await submitAmount(page, 120)
    expect(sse).toContain('"status":"success"')
    expect(sse).toContain('"rounds":1')
    expect(sse).toContain('"passed":true')
  })

  test('amount over the gate → crew stalls after stagnation', async ({ page }) => {
    const sse = await submitAmount(page, 900)
    expect(sse).toContain('"status":"stalled"')
    expect(sse).toContain('"rounds":2')
    expect(sse).toContain('"passed":false')
    expect(sse).not.toContain('"status":"success"')
  })
})

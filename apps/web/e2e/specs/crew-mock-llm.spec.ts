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
 * Crew loop with a model judge, wired the way the product teaches it:
 * a LINEAR chain trigger.chat_app → ai.agent_crew → action.agent (maker)
 * → action.evaluator (checker). The round result is the chain TERMINAL's
 * output (the evaluator's verdict, with the judged content passed
 * through) — this exact shape used to exhaust every round because
 * _execute_subgraph returned the START node's output.
 *
 * The mock LLM answers the maker with "Echo: <message>" and the judge
 * prompt with {"passed": true, "quality": 9, feedback} — so the crew must
 * terminate `success` in round 1 AND the maker's answer must reach the
 * visitor as the assistant reply.
 *
 * The judge references the maker via the legacy `{{agent.output.content}}`
 * path ($node('Agent') needs paired-item provenance that sub-graph start
 * nodes don't have).
 */

const TITLE = `E2E Judge ${Date.now()}`
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
        'crew',
        'ai.agent_crew',
        'Crew',
        { goal: 'answer', maxRounds: 2, minRounds: 1 },
        { x: 240, y: 0 },
      ),
      node(
        'agent',
        'action.agent',
        'Agent',
        {
          provider: 'openai',
          credential: credentialId,
          messages: [{ role: 'user', content: '{{$step.message}}' }],
        },
        { x: 480, y: 0 },
      ),
      node(
        'judge',
        'action.evaluator',
        'Judge',
        {
          provider: 'openai',
          credential: credentialId,
          content: '{{agent.output.content}}',
          metrics: [{ name: 'quality', description: 'q', min: 0, max: 10 }],
        },
        { x: 720, y: 0 },
      ),
    ],
    edges: [edge('trig', 'crew'), edge('crew', 'agent'), edge('agent', 'judge')],
  })
})

test.describe('crew loop — mock LLM judge', () => {
  test('linear maker → judge chain succeeds and the answer reaches the visitor', async ({
    page,
  }) => {
    await page.goto(`/apps/${ws}/${SLUG}`)
    await expect(
      page.getByRole('heading', { name: `Talk to ${TITLE}` }),
    ).toBeVisible()
    await page.waitForLoadState('networkidle')

    const streamDone = page.waitForResponse((r) => r.url().includes('/stream/'), {
      timeout: 60_000,
    })
    const input = page.getByPlaceholder(`Message ${TITLE}`)
    await input.fill('what is fuse')
    await input.press('Enter')

    await expect(page.getByText('what is fuse').first()).toBeVisible()

    const sse = await (await streamDone).text()

    // Round 1: maker echoed, judge scored it 9/10 and passed → success.
    expect(sse).toContain('"terminal_state":"success"')
    expect(sse).toContain('"rounds":1')
    expect(sse).toContain('"passed":true')
    // The judge verdict came from the mock model's metric path — proof the
    // evaluator called the LLM with the metrics prompt.
    expect(sse).toContain('mock judge: looks good')
    expect(sse).toContain('"quality":9')

    // The maker's answer survives the verdict node (content pass-through)
    // and lands in the transcript as the assistant reply.
    await expect(page.getByText('Echo: what is fuse')).toBeVisible({
      timeout: 60_000,
    })
  })
})

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
 * Crew loop with a model judge: trigger.chat_app → ai.agent_crew with a
 * maker (action.agent) and a checker (action.evaluator) as round members.
 * The mock LLM answers the maker with "Echo: <message>" and the judge
 * prompt with {"passed": true, "quality": 9, feedback} — so the crew must
 * terminate `success` in round 1 with the verdict attached.
 *
 * Graph shape note: the maker and checker hang as SIBLING successors of
 * the crew (crew→agent, crew→judge), not as a linear chain. A linear
 * crew → agent → evaluator chain never surfaces the checker's verdict:
 * WorkflowRunner._execute_subgraph returns the START node's output while
 * agent_crew reads sub[-1] as the round verdict — see the suspected-bug
 * notes in the PR. With siblings, run_downstream returns one output per
 * successor and sub[-1] is genuinely the evaluator's verdict.
 *
 * The judge references the maker via the legacy `{{agent.output.content}}`
 * path ($node('Agent') needs paired-item provenance that sub-graph start
 * nodes don't have).
 *
 * Outcome is asserted from the SSE stream the page opens (app runs have
 * no execution row): the execution_completed frame carries the crew
 * output. The maker's "Echo:" content is judged (quality 9 → passed) but
 * the crew's terminal output exposes only the verdict, so the visible
 * assistant entry is the empty state — asserted as proof the turn closed.
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
        { x: 480, y: -100 },
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
        { x: 480, y: 100 },
      ),
    ],
    // Order matters twice: successors run in edge order (maker before
    // judge), and the crew reads the LAST successor's output as the
    // round verdict.
    edges: [edge('trig', 'crew'), edge('crew', 'agent'), edge('crew', 'judge')],
  })
})

test.describe('crew loop — mock LLM judge', () => {
  test('judge passes the maker output → crew succeeds in round 1', async ({
    page,
  }) => {
    await page.goto(`/apps/${ws}/${SLUG}`)
    await expect(
      page.getByRole('heading', { name: `Talk to ${TITLE}` }),
    ).toBeVisible()
    // Wait for the conversation query to hydrate: useAppendMessage drops
    // optimistic entries while its cache is still empty.
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

    // Turn closes on the page. Crew output carries no `content`, so the
    // assistant entry renders the empty state (see header note).
    await expect(page.getByText('No response produced.')).toBeVisible({
      timeout: 60_000,
    })
  })
})

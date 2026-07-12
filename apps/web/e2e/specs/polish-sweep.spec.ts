/**
 * Polish sweep — NOT a pass/fail suite. Walks every screen and captures
 * the deterministic phase-6 gaps: console errors/warnings, 375px
 * horizontal scroll, and a screenshot per screen. Writes a machine-
 * readable report to e2e/.polish/report.json for triage.
 *
 * Run: npx playwright test e2e/polish-sweep.spec.ts --reporter=line
 * Then read e2e/.polish/report.json.
 *
 * Uses the seeded storageState (logged in). A workflow + crew are created
 * via API so the editor screens have real graphs.
 */
import fs from 'node:fs'

import { expect, test } from '@playwright/test'

import { createWorkflow, edge, node, seededToken } from '../api'

type ScreenReport = {
  name: string
  path: string
  consoleErrors: string[]
  consoleWarnings: string[]
  pageErrors: string[]
  failedRequests: string[]
  horizontalScroll375: boolean
}

const OUT = 'e2e/.polish'
const reports: ScreenReport[] = []

// Opt-in only: this is a diagnostic sweep, not a gate. CI stays fast.
test.skip(!process.env.POLISH, 'polish sweep runs only with POLISH=1')

let workflowId = ''
let crewId = ''

test.beforeAll(async () => {
  const token = seededToken()
  const wf = await createWorkflow(token, `Polish WF ${Date.now()}`, {
    nodes: [
      node('start', 'trigger.manual', 'Start', {}),
      node('code', 'logic.code', 'Code', { language: 'python', code: "output = {'ok': True}" }, { x: 260, y: 0 }),
    ],
    edges: [edge('start', 'code')],
  })
  workflowId = wf.id
  // A crew too (kind=crew editor differences).
  const { API } = await import('../api')
  const { apiContext } = await import('../api')
  const ctx = await apiContext(token)
  const res = await ctx.post(`${API}/crews/`, {
    data: {
      name: `Polish Crew ${Date.now()}`,
      graph: {
        nodes: [node('chat', 'trigger.chat_app', 'Chat', { title: 'Polish Crew' })],
        edges: [],
      },
    },
  })
  if (res.ok()) crewId = (await res.json()).id
  fs.mkdirSync(OUT, { recursive: true })
})

const SCREENS: Array<{ name: string; path: () => string; auth?: boolean }> = [
  { name: 'dashboard', path: () => '/dashboard' },
  { name: 'automations', path: () => '/automations' },
  { name: 'templates-gallery', path: () => '/templates' },
  { name: 'my-templates', path: () => '/templates/mine' },
  { name: 'crew-templates', path: () => '/loops/templates' },
  { name: 'personas', path: () => '/loops/personas' },
  { name: 'runs', path: () => '/runs' },
  { name: 'schedules', path: () => '/schedules' },
  { name: 'logs', path: () => '/logs' },
  { name: 'tables', path: () => '/tables' },
  { name: 'files', path: () => '/files' },
  { name: 'knowledge', path: () => '/knowledge' },
  { name: 'skills', path: () => '/skills' },
  { name: 'variables', path: () => '/variables' },
  { name: 'connections', path: () => '/connections' },
  { name: 'settings', path: () => '/settings' },
  { name: 'workspace-settings', path: () => '/settings/workspace' },
  { name: 'workflow-editor', path: () => `/workflows/${workflowId}` },
  { name: 'crew-editor', path: () => `/crews/${crewId}` },
  { name: 'not-found', path: () => '/this-route-does-not-exist' },
]

for (const screen of SCREENS) {
  test(`sweep: ${screen.name}`, async ({ page }) => {
    const r: ScreenReport = {
      name: screen.name,
      path: '',
      consoleErrors: [],
      consoleWarnings: [],
      pageErrors: [],
      failedRequests: [],
      horizontalScroll375: false,
    }
    page.on('console', (msg) => {
      const t = msg.type()
      if (t === 'error') r.consoleErrors.push(msg.text().slice(0, 300))
      else if (t === 'warning') r.consoleWarnings.push(msg.text().slice(0, 300))
    })
    page.on('pageerror', (err) => r.pageErrors.push(String(err).slice(0, 300)))
    page.on('requestfailed', (req) => {
      const u = req.url()
      if (!u.startsWith('data:')) r.failedRequests.push(`${req.method()} ${u.slice(0, 160)}`)
    })

    const path = screen.path()
    r.path = path
    await page.goto(path)
    // Let async data settle without failing the sweep on slow endpoints.
    await page.waitForLoadState('networkidle').catch(() => {})
    await page.waitForTimeout(1200)

    // Desktop screenshot.
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.waitForTimeout(200)
    await page.screenshot({ path: `${OUT}/${screen.name}-desktop.png` }).catch(() => {})

    // Mobile 375: horizontal-scroll check.
    await page.setViewportSize({ width: 375, height: 812 })
    await page.waitForTimeout(300)
    r.horizontalScroll375 = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2,
    )
    await page.screenshot({ path: `${OUT}/${screen.name}-mobile.png` }).catch(() => {})

    reports.push(r)
    expect(true).toBe(true) // sweep never fails; the report is the output
  })
}

test.afterAll(async () => {
  fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(reports, null, 2))
})

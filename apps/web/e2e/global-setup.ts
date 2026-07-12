/**
 * Seeds the e2e stack (test user + mock LLM credential) and saves a
 * logged-in browser storage state every spec reuses.
 */
import fs from 'node:fs'

import { chromium } from '@playwright/test'

import { API, BASE, USER, apiContext, ensureMockCredential, registerAndLogin, seededToken } from './api'

export default async function globalSetup() {
  // Auth endpoints are rate-limited to 5/minute — a full setup spends 3
  // (register + API login + UI login), so back-to-back `playwright test`
  // invocations trip 429s. Reuse the saved state when its token is alive.
  try {
    const saved = seededToken()
    const me = await (await apiContext(saved)).get(`${API}/auth/me`)
    if (me.ok()) return
  } catch {
    // No saved state yet (or it expired) — do the full seed below.
  }

  const token = await registerAndLogin()
  await ensureMockCredential(token)

  // Login through the real UI once so whatever the app stores
  // (localStorage token, cookies) is captured faithfully.
  const browser = await chromium.launch()
  const page = await browser.newPage()
  await page.goto(`${BASE}/login`)
  // FormField labels aren't wired to inputs (htmlFor id never injected)
  // — placeholder selectors until that's fixed.
  await page.getByPlaceholder('you@company.com').fill(USER.email)
  await page.getByPlaceholder('Your password').fill(USER.password)
  await page.getByRole('button', { name: 'Continue with email' }).click()
  await page.waitForURL(/dashboard|automations|home/i, { timeout: 20_000 })

  // Relative to apps/web (playwright's cwd) — matches config storageState.
  fs.mkdirSync('e2e/.auth', { recursive: true })
  await page.context().storageState({ path: 'e2e/.auth/user.json' })
  await browser.close()
}

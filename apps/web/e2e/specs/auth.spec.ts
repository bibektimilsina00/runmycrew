import { expect, test } from '@playwright/test'

import { USER } from '../api'

// Uses NO storageState — exercises the real register/login UI.
test.use({ storageState: { cookies: [], origins: [] } })

test.describe('auth', () => {
  test('register → login → dashboard', async ({ page }) => {
    const email = `auth-${Date.now()}@example.com`

    await page.goto('/register')
    await page.getByPlaceholder('you@company.com').fill(email)
    await page.getByPlaceholder('Create a password').fill(USER.password)
    await page.getByRole('button', { name: 'Create account' }).click()

    // Either lands straight in the app or on /login — accept both, then log in if needed.
    await page.waitForLoadState('networkidle')
    if (page.url().includes('/login')) {
      await page.getByPlaceholder('you@company.com').fill(email)
      await page.getByPlaceholder('Your password').fill(USER.password)
      await page.getByRole('button', { name: 'Continue with email' }).click()
    }
    await page.waitForURL(/dashboard|automations|home/i, { timeout: 20_000 })
    await expect(page.getByRole('link', { name: 'Home' })).toBeVisible()
  })

  test('login with seeded user lands on dashboard', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('you@company.com').fill(USER.email)
    await page.getByPlaceholder('Your password').fill(USER.password)
    await page.getByRole('button', { name: 'Continue with email' }).click()
    await page.waitForURL(/dashboard|automations|home/i, { timeout: 20_000 })
  })
})

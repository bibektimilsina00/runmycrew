import { defineConfig } from '@playwright/test'

/**
 * E2E suite against the docker-compose.e2e.yml stack (web on :4700).
 * Bring it up first: pnpm e2e:up (always --build — stale workers lie).
 */
export default defineConfig({
  testDir: './e2e/specs',
  globalSetup: './e2e/global-setup.ts',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false, // scenarios share one seeded workspace
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:4700',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    storageState: 'e2e/.auth/user.json',
  },
})

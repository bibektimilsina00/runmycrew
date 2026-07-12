/** Thin typed helpers over the API for seeding and assertions. */
import fs from 'node:fs'

import { APIRequestContext, request } from '@playwright/test'

export const BASE = process.env.E2E_BASE_URL || 'http://localhost:4700'
export const API = `${BASE}/api/v1`

export const USER = {
  email: 'e2e@example.com',
  password: 'E2ePassw0rd!x',
  full_name: 'E2E Runner',
}

export async function apiContext(token?: string): Promise<APIRequestContext> {
  // NB: no baseURL — Playwright resolves a leading-slash path against
  // the origin and silently drops the /api/v1 prefix. Absolute URLs only.
  return request.newContext({
    extraHTTPHeaders: token ? { Authorization: `Bearer ${token}` } : {},
  })
}

/**
 * The seeded user's token, straight from the storage state globalSetup
 * saved — zero /auth calls, which matters: auth endpoints are limited to
 * 5/minute per IP (RATE_LIMIT_AUTH) and globalSetup already spends 3.
 */
export function seededToken(): string {
  const state = JSON.parse(fs.readFileSync('e2e/.auth/user.json', 'utf8')) as {
    origins: { origin: string; localStorage: { name: string; value: string }[] }[]
  }
  for (const origin of state.origins) {
    const hit = origin.localStorage.find((i) => i.name === 'runmycrew-auth-token')
    if (hit) return hit.value
  }
  throw new Error('runmycrew-auth-token not found in e2e/.auth/user.json')
}

/** POST that waits out the 5/minute auth rate limit once before giving up. */
async function postAuth(
  ctx: APIRequestContext,
  url: string,
  data: Record<string, unknown>,
) {
  let res = await ctx.post(url, { data })
  if (res.status() === 429) {
    const retryAfter = Number((await res.json().catch(() => ({})))?.retry_after) || 60
    await new Promise((r) => setTimeout(r, Math.min(retryAfter, 65) * 1000 + 500))
    res = await ctx.post(url, { data })
  }
  return res
}

export async function registerAndLogin(
  email = USER.email,
  password = USER.password,
): Promise<string> {
  const ctx = await apiContext()
  // Idempotent: register may 400 on re-runs against a warm stack.
  await postAuth(ctx, `${API}/auth/register`, {
    email,
    password,
    full_name: USER.full_name,
  })
  const login = await postAuth(ctx, `${API}/auth/login`, { email, password })
  if (!login.ok()) throw new Error(`login failed: ${login.status()} ${await login.text()}`)
  const body = await login.json()
  return body.access_token as string
}

export async function ensureMockCredential(token: string): Promise<string> {
  const ctx = await apiContext(token)
  const existing = await (await ctx.get(`${API}/credentials/`)).json()
  const hit = Array.isArray(existing)
    ? existing.find((c: { type: string }) => c.type === 'openai_api_key')
    : undefined
  if (hit) return hit.id as string
  const created = await ctx.post(`${API}/credentials/`, {
    data: {
      name: 'Mock OpenAI',
      type: 'openai_api_key',
      data: { api_key: 'sk-e2e-mock-key' },
    },
  })
  if (!created.ok()) throw new Error(`credential failed: ${await created.text()}`)
  return (await created.json()).id as string
}

export async function createWorkflow(
  token: string,
  name: string,
  graph: unknown,
): Promise<{ id: string }> {
  const ctx = await apiContext(token)
  const res = await ctx.post(`${API}/workflows/`, { data: { name, graph } })
  if (!res.ok()) throw new Error(`workflow create failed: ${await res.text()}`)
  return res.json()
}

/** Mirrors apps/api/app/features/apps/repository.py::_slugify. */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

export async function workspaceSlug(token: string): Promise<string> {
  const ctx = await apiContext(token)
  const res = await ctx.get(`${API}/workspaces/`)
  if (!res.ok()) throw new Error(`workspaces failed: ${await res.text()}`)
  const rows = (await res.json()) as { slug: string }[]
  if (!rows.length) throw new Error('seeded user has no workspace')
  return rows[0].slug
}

/** Create a crew (workflow row with kind=crew) and flip it live. */
export async function createActiveCrew(
  token: string,
  name: string,
  graph: unknown,
): Promise<{ id: string }> {
  const ctx = await apiContext(token)
  const created = await ctx.post(`${API}/crews/`, { data: { name, graph } })
  if (!created.ok()) throw new Error(`crew create failed: ${await created.text()}`)
  const crew = (await created.json()) as { id: string }
  const toggled = await ctx.post(`${API}/crews/${crew.id}/toggle`)
  if (!toggled.ok()) throw new Error(`crew toggle failed: ${await toggled.text()}`)
  const state = (await toggled.json()) as { is_active: boolean }
  if (!state.is_active) throw new Error('crew did not activate on toggle')
  return crew
}

export function node(
  id: string,
  type: string,
  label: string,
  properties: Record<string, unknown>,
  position = { x: 0, y: 0 },
) {
  return { id, type, position, data: { label, properties } }
}

export function edge(source: string, target: string) {
  return { id: `${source}-${target}`, source, target }
}

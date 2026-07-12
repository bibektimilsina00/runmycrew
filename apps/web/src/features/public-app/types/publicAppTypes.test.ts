/**
 * Real API payloads vs the zod schemas that parse them.
 *
 * Every fixture in __fixtures__/ was captured verbatim from the running
 * API (scratchpad capture script, 2026-07-12) — not hand-written. If the
 * backend reshapes a response, re-capture; if a schema tightens, these
 * fail before prod does. The crew-owned session with `workflow_id: null`
 * is the canonical regression: SessionSchema once required a string and
 * the public chat page crashed for every crew app.
 */
import { describe, expect, it } from 'vitest'

import appConfigCrewChat from '../__fixtures__/app_config_crew_chat.json'
import appConfigWorkflowChat from '../__fixtures__/app_config_workflow_chat.json'
import appConfigWorkflowForm from '../__fixtures__/app_config_workflow_form.json'
import history from '../__fixtures__/history.json'
import sendMessageOut from '../__fixtures__/send_message_out.json'
import sessionEnvelopeCrew from '../__fixtures__/session_envelope_crew.json'
import sessionEnvelopeWorkflow from '../__fixtures__/session_envelope_workflow.json'
import sessionListCrew from '../__fixtures__/session_list_crew.json'
import sessionListWorkflow from '../__fixtures__/session_list_workflow.json'
import {
  AppMessageSchema,
  PublicAppSchema,
  SendMessageOutSchema,
  SessionEnvelopeSchema,
  SessionListSchema,
  SessionSchema,
} from './publicAppTypes'

describe('PublicAppSchema vs real payloads', () => {
  it.each([
    ['workflow-owned chat app', appConfigWorkflowChat],
    ['crew-owned chat app', appConfigCrewChat],
    ['workflow-owned form app', appConfigWorkflowForm],
  ])('parses the %s config', (_label, fixture) => {
    const parsed = PublicAppSchema.parse(fixture)
    expect(parsed.workspace_slug).toBeTruthy()
    expect(parsed.app_slug).toBeTruthy()
  })
})

describe('SessionEnvelopeSchema vs real payloads', () => {
  it('parses a workflow-owned session envelope', () => {
    const parsed = SessionEnvelopeSchema.parse(sessionEnvelopeWorkflow)
    expect(parsed.session.workflow_id).toBeTruthy()
  })

  it('parses a crew-owned session envelope (workflow_id: null — the shipped crash)', () => {
    const parsed = SessionEnvelopeSchema.parse(sessionEnvelopeCrew)
    expect(parsed.session.workflow_id).toBeNull()
    expect(parsed.session.crew_id).toBeTruthy()
  })

  it('SessionSchema alone accepts null workflow_id and null user_id', () => {
    const parsed = SessionSchema.parse(sessionEnvelopeCrew.session)
    expect(parsed.workflow_id).toBeNull()
    expect(parsed.user_id).toBeNull()
  })
})

describe('SessionListSchema vs real payloads', () => {
  it.each([
    ['workflow-owned', sessionListWorkflow],
    ['crew-owned', sessionListCrew],
  ])('parses the %s session list', (_label, fixture) => {
    const parsed = SessionListSchema.parse(fixture)
    expect(Array.isArray(parsed.sessions)).toBe(true)
  })
})

describe('AppMessageSchema vs real payloads', () => {
  it('parses every message in a real history response (user + assistant)', () => {
    expect((history as unknown[]).length).toBeGreaterThanOrEqual(2)
    const roles = new Set<string>()
    for (const message of history as unknown[]) {
      roles.add(AppMessageSchema.parse(message).role)
    }
    expect(roles.has('user')).toBe(true)
  })
})

describe('SendMessageOutSchema vs real payloads', () => {
  it('parses the message-accepted envelope', () => {
    const parsed = SendMessageOutSchema.parse(sendMessageOut)
    expect(parsed.execution_id).toMatch(/^app-/)
    expect(parsed.stream_url).toContain(parsed.execution_id)
  })
})

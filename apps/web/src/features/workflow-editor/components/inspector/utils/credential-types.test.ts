import { describe, expect, it } from 'vitest'
import type { NodeDefinition, NodeProperty } from '../../../types/editorTypes'
import { resolveCredentialTypes } from './credential-types'

const prop = (overrides: Partial<NodeProperty> & { name: string }): NodeProperty => ({
  label: overrides.name,
  type: 'credential',
  ...overrides,
})

const definition = (overrides: Partial<NodeDefinition> = {}): NodeDefinition => ({
  type: 'test_node',
  name: 'Test Node',
  category: 'integration',
  description: '',
  icon: 'plug',
  properties: [],
  inputs: 1,
  outputs: 1,
  ...overrides,
})

describe('resolveCredentialTypes', () => {
  it('explicit credentialType string wins over everything', () => {
    const p = prop({
      name: 'credential',
      credentialType: 'slack_oauth',
      credentialTypeByField: { field: 'provider', values: { openai: 'openai_api' } },
    })
    const def = definition({ credentialType: 'other' })
    expect(resolveCredentialTypes(p, def, { provider: 'openai' })).toEqual(['slack_oauth'])
  })

  it('explicit credentialType array is returned as-is', () => {
    const p = prop({ name: 'credential', credentialType: ['gmail_oauth', 'google_api_key'] })
    expect(resolveCredentialTypes(p, definition(), {})).toEqual(['gmail_oauth', 'google_api_key'])
  })

  it('credentialTypeByField maps the current property value when present', () => {
    const p = prop({
      name: 'credential',
      credentialTypeByField: {
        field: 'provider',
        values: { openai: 'openai_api', anthropic: 'anthropic_api' },
      },
    })
    expect(resolveCredentialTypes(p, definition(), { provider: 'anthropic' })).toEqual([
      'anthropic_api',
    ])
  })

  it('falls back to the driving field\'s declared default when no value is set (fresh-node regression)', () => {
    // A freshly dropped node has no persisted `provider`; without the
    // default fallback the selector rendered "does not declare a
    // credential type" until the user re-picked the provider.
    const p = prop({
      name: 'credential',
      credentialTypeByField: { field: 'provider', values: { openai: 'openai_api' } },
    })
    const def = definition({
      properties: [
        { name: 'provider', label: 'Provider', type: 'options', default: 'openai' },
        p,
      ],
    })
    expect(resolveCredentialTypes(p, def, {})).toEqual(['openai_api'])
  })

  it('explicit current value wins over the driving field default', () => {
    const p = prop({
      name: 'credential',
      credentialTypeByField: {
        field: 'provider',
        values: { openai: 'openai_api', anthropic: 'anthropic_api' },
      },
    })
    const def = definition({
      properties: [{ name: 'provider', label: 'Provider', type: 'options', default: 'openai' }],
    })
    expect(resolveCredentialTypes(p, def, { provider: 'anthropic' })).toEqual(['anthropic_api'])
  })

  it('returns [] when the value has no mapping and the driver declares no default', () => {
    const p = prop({
      name: 'credential',
      credentialTypeByField: { field: 'provider', values: { openai: 'openai_api' } },
    })
    // Value present but unmapped
    expect(resolveCredentialTypes(p, definition(), { provider: 'custom' })).toEqual([])
    // No value, driver missing from definition
    expect(resolveCredentialTypes(p, definition(), {})).toEqual([])
  })

  it('does NOT fall back to a dynamic default over an empty [] when the definition credentialType is set', () => {
    // credentialTypeByField is an exclusive branch: an unresolved dynamic
    // mapping yields [], it must not leak into definition.credentialType.
    const p = prop({
      name: 'credential',
      credentialTypeByField: { field: 'provider', values: { openai: 'openai_api' } },
    })
    const def = definition({ credentialType: 'fallback_cred' })
    expect(resolveCredentialTypes(p, def, { provider: 'unmapped' })).toEqual([])
  })

  it('plain credential field resolves the definition-level credentialType', () => {
    const p = prop({ name: 'credential' })
    const def = definition({ credentialType: 'github_oauth' })
    expect(resolveCredentialTypes(p, def, {})).toEqual(['github_oauth'])
  })

  it('returns [] when nothing declares a credential type', () => {
    expect(resolveCredentialTypes(prop({ name: 'credential' }), definition(), {})).toEqual([])
  })
})

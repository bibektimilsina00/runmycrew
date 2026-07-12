import { describe, expect, it } from 'vitest'
import type { NodeProperty } from '../../../types/editorTypes'
import {
  getDefaultPropertyValue,
  splitPropertyGroups,
  valuesWithDefaults,
} from './inspector-visibility'

const prop = (overrides: Partial<NodeProperty> & { name: string }): NodeProperty => ({
  label: overrides.name,
  type: 'string',
  ...overrides,
})

const basicNames = (props: NodeProperty[], values: Record<string, unknown> = {}) =>
  splitPropertyGroups(props, values).basicGroups.flatMap(g => g.properties.map(p => p.name))

describe('getDefaultPropertyValue', () => {
  it('returns the declared default when present', () => {
    expect(getDefaultPropertyValue(prop({ name: 'op', type: 'options', default: 'send' }))).toBe('send')
  })

  it('falls back per type when no default is declared', () => {
    expect(getDefaultPropertyValue(prop({ name: 'a', type: 'boolean' }))).toBe(false)
    expect(getDefaultPropertyValue(prop({ name: 'b', type: 'number' }))).toBe(0)
    expect(getDefaultPropertyValue(prop({ name: 'c', type: 'key-value' }))).toEqual({})
    expect(getDefaultPropertyValue(prop({ name: 'd', type: 'list' }))).toEqual([])
    expect(getDefaultPropertyValue(prop({ name: 'e', type: 'string' }))).toBe('')
  })

  it('collection default depends on multipleValues', () => {
    expect(
      getDefaultPropertyValue(prop({ name: 'c', type: 'collection', typeOptions: { multipleValues: true } })),
    ).toEqual([])
    expect(getDefaultPropertyValue(prop({ name: 'c', type: 'collection' }))).toEqual({})
  })
})

describe('valuesWithDefaults', () => {
  it('fills missing values from property defaults, saved values win', () => {
    const defs = [
      prop({ name: 'operation', type: 'options', default: 'send_email' }),
      prop({ name: 'to', default: '' }),
    ]
    expect(valuesWithDefaults(defs, {})).toEqual({ operation: 'send_email', to: '' })
    expect(valuesWithDefaults(defs, { operation: 'create_draft' })).toEqual({
      operation: 'create_draft',
      to: '',
    })
  })

  it('leaves properties without defaults absent', () => {
    expect(valuesWithDefaults([prop({ name: 'q' })], {})).toEqual({})
  })
})

describe('splitPropertyGroups — ordering', () => {
  it('hoists the action select first and a plain credential second (integration node shape)', () => {
    // Real integration nodes declare credential first; the inspector flips it.
    const defs = [
      prop({ name: 'credential', type: 'credential', credentialType: 'slack_oauth' }),
      prop({ name: 'operation', type: 'options', default: 'send_message', options: [] }),
      prop({ name: 'channel' }),
    ]
    expect(basicNames(defs)).toEqual(['operation', 'credential', 'channel'])
  })

  it('does NOT hoist a credentialTypeByField credential above its driving field', () => {
    const defs = [
      prop({ name: 'provider', type: 'options', default: 'openai' }),
      prop({
        name: 'credential',
        type: 'credential',
        credentialTypeByField: { field: 'provider', values: { openai: 'openai_api' } },
      }),
      prop({ name: 'model' }),
    ]
    // Declared order preserved: credential stays after provider.
    expect(basicNames(defs)).toEqual(['provider', 'credential', 'model'])
  })

  it('does NOT hoist a dependsOn credential above its driver', () => {
    const defs = [
      prop({ name: 'provider', type: 'options', default: 'openai' }),
      prop({ name: 'credential', type: 'credential', dependsOn: ['provider'] }),
    ]
    expect(basicNames(defs)).toEqual(['provider', 'credential'])
  })

  it('dependent credential is not hoisted even when an action field exists', () => {
    const defs = [
      prop({ name: 'provider', type: 'options', default: 'openai' }),
      prop({
        name: 'credential',
        type: 'credential',
        credentialTypeByField: { field: 'provider', values: { openai: 'openai_api' } },
      }),
      prop({ name: 'operation', type: 'options', default: 'chat' }),
    ]
    // operation jumps first; provider/credential keep declared relative order.
    expect(basicNames(defs)).toEqual(['operation', 'provider', 'credential'])
  })

  it('only exact action names of type options are hoisted', () => {
    const defs = [
      prop({ name: 'cron_expression' }),
      prop({ name: 'update_operation_id' }),
      prop({ name: 'operation' }), // type string — not hoisted
      prop({ name: 'method', type: 'options' }),
    ]
    expect(basicNames(defs)).toEqual(['method', 'cron_expression', 'update_operation_id', 'operation'])
  })

  it('is stable: equal-priority properties keep declared order', () => {
    const defs = [prop({ name: 'a' }), prop({ name: 'b' }), prop({ name: 'c' })]
    expect(basicNames(defs)).toEqual(['a', 'b', 'c'])
  })
})

describe('splitPropertyGroups — visibility and grouping', () => {
  it('filters hidden properties and splits advanced into advancedGroups', () => {
    const defs = [
      prop({ name: 'shown' }),
      prop({ name: 'secret_internal', visibility: 'hidden' }),
      prop({ name: 'timeout', mode: 'advanced' }),
    ]
    const { basicGroups, advancedGroups } = splitPropertyGroups(defs, {})
    expect(basicGroups.flatMap(g => g.properties.map(p => p.name))).toEqual(['shown'])
    expect(advancedGroups.flatMap(g => g.properties.map(p => p.name))).toEqual(['timeout'])
  })

  it('evaluates conditions against defaults so a fresh node shows gated fields', () => {
    const defs = [
      prop({ name: 'operation', type: 'options', default: 'send_email' }),
      prop({ name: 'to', condition: { field: 'operation', value: 'send_email' } }),
      prop({ name: 'draft_id', condition: { field: 'operation', value: 'create_draft' } }),
    ]
    expect(basicNames(defs, {})).toEqual(['operation', 'to'])
    expect(basicNames(defs, { operation: 'create_draft' })).toEqual(['operation', 'draft_id'])
  })

  it('groups by prop.group with "Settings" as the fallback bucket', () => {
    const defs = [
      prop({ name: 'a' }),
      prop({ name: 'token', group: 'Auth' }),
      prop({ name: 'b' }),
    ]
    const { basicGroups } = splitPropertyGroups(defs, {})
    expect(basicGroups.map(g => g.name)).toEqual(['Settings', 'Auth'])
    expect(basicGroups[0].properties.map(p => p.name)).toEqual(['a', 'b'])
    expect(basicGroups[1].properties.map(p => p.name)).toEqual(['token'])
  })
})

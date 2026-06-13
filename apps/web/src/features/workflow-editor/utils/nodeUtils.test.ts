import { describe, expect, it } from 'vitest'
import { getPropValuePreview } from './nodeUtils'

describe('getPropValuePreview — design-time expression resolution', () => {
  it('resolves pure arithmetic', () => {
    expect(getPropValuePreview('=1+1', 'string')).toBe('2')
    expect(getPropValuePreview('=2*3-1', 'string')).toBe('5')
    expect(getPropValuePreview('=(2+3)*4', 'string')).toBe('20')
  })

  it('resolves a standalone string literal', () => {
    expect(getPropValuePreview('="hello"', 'string')).toBe('hello')
  })

  it('resolves string concat between quoted parts', () => {
    // Result is "ab" (3 chars); below the 10-char truncation so no ellipsis.
    expect(getPropValuePreview('="a" & "b"', 'string')).toBe('ab')
  })

  it('truncates long resolved strings the same as plain ones', () => {
    expect(getPropValuePreview('="abcdefghijklmnop"', 'string')).toBe('abcdefghij…')
  })

  it('falls back to raw text for runtime references', () => {
    // Anything outside the design-time subset shows the raw expression
    // (truncated by the existing 10-char rule).
    expect(getPropValuePreview('=$step.x', 'string')).toBe('=$step.x')
    expect(getPropValuePreview('=$trigger.url', 'string')).toBe('=$trigger.…')
    expect(getPropValuePreview('=$node("X").y', 'string')).toBe('=$node("X"…')
  })

  it('falls back to raw text for JSONata function calls', () => {
    // Function calls aren't in the safe subset — we don't try to evaluate
    // `$sum(...)` synchronously.
    expect(getPropValuePreview('=$sum([1,2,3])', 'string')).toBe('=$sum([1,2…')
  })

  it('falls back for arithmetic-shaped expressions that produce non-finite results', () => {
    // 1/0 = Infinity; Number.isFinite rejects it, so the raw text shows.
    expect(getPropValuePreview('=1/0', 'string')).toBe('=1/0')
  })

  it('preserves the boolean / json / list / empty branches', () => {
    expect(getPropValuePreview(true, 'boolean')).toBe('True')
    expect(getPropValuePreview({}, 'json')).toBe('...')
    expect(getPropValuePreview([1, 2, 3], 'list')).toBe('3 items')
    expect(getPropValuePreview('', 'string')).toBe('-')
    expect(getPropValuePreview(null, 'string')).toBe('-')
  })

  it('leaves non-expression strings on the existing format path', () => {
    expect(getPropValuePreview('plain text', 'string')).toBe('plain text')
    expect(getPropValuePreview('much longer than ten chars', 'string')).toBe('much longe…')
  })
})

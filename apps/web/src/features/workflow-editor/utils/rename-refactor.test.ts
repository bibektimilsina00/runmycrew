import { describe, expect, it } from 'vitest'
import type { Node } from 'reactflow'
import {
  renameNodeInGraph,
  rewriteExpressionLabels,
  rewriteExpressionLabelsInString,
  validateNodeLabel,
} from './rename-refactor'

describe('rewriteExpressionLabelsInString', () => {
  it('rewrites single-quoted node calls', () => {
    expect(rewriteExpressionLabelsInString(`=$node('Foo').bar`, 'Foo', 'Bar'))
      .toBe(`=$node('Bar').bar`)
  })

  it('rewrites double-quoted node calls', () => {
    expect(rewriteExpressionLabelsInString(`=$node("Foo").bar`, 'Foo', 'Bar'))
      .toBe(`=$node("Bar").bar`)
  })

  it('preserves the original quote style on rewrite', () => {
    expect(rewriteExpressionLabelsInString(`=$node("Foo")`, 'Foo', 'Quux'))
      .toBe(`=$node("Quux")`)
  })

  it('leaves non-expression strings untouched even when they look like calls', () => {
    // Strings without leading `=` are plain text, never evaluated.
    expect(rewriteExpressionLabelsInString(`$node('Foo')`, 'Foo', 'Bar'))
      .toBe(`$node('Foo')`)
  })

  it('does not touch unrelated labels', () => {
    expect(rewriteExpressionLabelsInString(`=$node('Other').x`, 'Foo', 'Bar'))
      .toBe(`=$node('Other').x`)
  })

  it('rewrites every occurrence in one expression', () => {
    expect(
      rewriteExpressionLabelsInString(`=$node('Foo').a + $node('Foo').b`, 'Foo', 'Bar'),
    ).toBe(`=$node('Bar').a + $node('Bar').b`)
  })

  it('respects escaped quotes inside the label body', () => {
    // The user named the node `My "weird"` and uses it as $node("My \"weird\"").
    const src = `=$node("My \\"weird\\"").x`
    expect(rewriteExpressionLabelsInString(src, 'My "weird"', 'Renamed'))
      .toBe(`=$node("Renamed").x`)
  })

  it('re-escapes the replacement label to match the original quote style', () => {
    expect(rewriteExpressionLabelsInString(`=$node('Foo').x`, 'Foo', `O'Brien`))
      .toBe(`=$node('O\\'Brien').x`)
  })

  it('tolerates whitespace inside the call', () => {
    expect(rewriteExpressionLabelsInString(`=$node(  'Foo'  ).x`, 'Foo', 'Bar'))
      .toBe(`=$node('Bar').x`)
  })
})

describe('rewriteExpressionLabels (recursive)', () => {
  it('walks nested dicts and lists', () => {
    const input = {
      a: `=$node('Foo').x`,
      b: ['plain', `=$node('Foo').y`, 42],
      c: { nested: `=$node('Foo').z` },
    }
    expect(rewriteExpressionLabels(input, 'Foo', 'Bar')).toEqual({
      a: `=$node('Bar').x`,
      b: ['plain', `=$node('Bar').y`, 42],
      c: { nested: `=$node('Bar').z` },
    })
  })

  it('passes through non-strings unchanged', () => {
    expect(rewriteExpressionLabels(42, 'Foo', 'Bar')).toBe(42)
    expect(rewriteExpressionLabels(true, 'Foo', 'Bar')).toBe(true)
    expect(rewriteExpressionLabels(null, 'Foo', 'Bar')).toBe(null)
  })
})

describe('renameNodeInGraph', () => {
  const makeNodes = (): Node[] => [
    {
      id: 'a',
      type: 'logic.code',
      position: { x: 0, y: 0 },
      data: { label: 'Foo', properties: {} },
    },
    {
      id: 'b',
      type: 'logic.code',
      position: { x: 0, y: 0 },
      data: {
        label: 'B',
        properties: {
          code: `=$node('Foo').x + 1`,
          headers: { name: `=$node('Foo').headers."x-id"` },
          unrelated: 'plain text',
        },
      },
    },
    {
      id: 'c',
      type: 'logic.code',
      position: { x: 0, y: 0 },
      data: {
        label: 'C',
        properties: { code: `=$step.value` },
      },
    },
  ]

  it('updates the target node label', () => {
    const next = renameNodeInGraph(makeNodes(), 'a', 'Foo Renamed')
    expect(next[0].data.label).toBe('Foo Renamed')
  })

  it('rewrites references in every other node', () => {
    const next = renameNodeInGraph(makeNodes(), 'a', 'Foo Renamed')
    const bProps = next[1].data.properties as Record<string, unknown>
    expect(bProps.code).toBe(`=$node('Foo Renamed').x + 1`)
    expect((bProps.headers as Record<string, string>).name)
      .toBe(`=$node('Foo Renamed').headers."x-id"`)
    expect(bProps.unrelated).toBe('plain text')
  })

  it('leaves nodes with no references untouched (same reference identity)', () => {
    const before = makeNodes()
    const next = renameNodeInGraph(before, 'a', 'Foo Renamed')
    // Node `c` references `$step`, not `$node('Foo')` — same object back.
    expect(next[2]).toBe(before[2])
  })

  it('is a no-op when the label did not change', () => {
    const before = makeNodes()
    const next = renameNodeInGraph(before, 'a', 'Foo')
    expect(next).toBe(before)
  })

  it('returns input unchanged when the target id is unknown', () => {
    const before = makeNodes()
    const next = renameNodeInGraph(before, 'missing', 'X')
    expect(next).toBe(before)
  })
})

describe('validateNodeLabel', () => {
  const nodes: Node[] = [
    { id: 'a', type: 'x', position: { x: 0, y: 0 }, data: { label: 'Alpha' } },
    { id: 'b', type: 'x', position: { x: 0, y: 0 }, data: { label: 'Beta' } },
  ]

  it('rejects an empty label', () => {
    expect(validateNodeLabel('a', '', nodes)).toBe('Label cannot be empty')
    expect(validateNodeLabel('a', '   ', nodes)).toBe('Label cannot be empty')
  })

  it('rejects a label used by a different node', () => {
    expect(validateNodeLabel('a', 'Beta', nodes)).toBe('Label already used by another node')
  })

  it('allows a node to keep its own label', () => {
    expect(validateNodeLabel('a', 'Alpha', nodes)).toBeNull()
  })

  it('accepts a fresh label', () => {
    expect(validateNodeLabel('a', 'Gamma', nodes)).toBeNull()
  })

  it('compares trimmed values for the duplicate check', () => {
    expect(validateNodeLabel('a', '  Beta  ', nodes)).toBe('Label already used by another node')
  })
})

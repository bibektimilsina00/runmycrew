/**
 * Tiny JSONata-ish tokenizer for the highlight overlay.
 *
 * Splits the body of a `{{ … }}` block into typed tokens so each can get
 * its own Tailwind colour class. The grammar isn't a strict JSONata parse
 * — we just want the same look-and-feel as VS Code / a Prism theme: a
 * different colour per "kind of thing" the user is looking at.
 *
 * Order matters: longer / more-specific patterns come first so we don't
 * eat `$step` as a bare identifier.
 */

export type TokenKind =
  | 'whitespace'
  | 'string'
  | 'number'
  | 'variable'
  | 'function'
  | 'property'
  | 'punctuation'
  | 'operator'
  | 'identifier'
  | 'unknown'

export interface Token {
  kind: TokenKind
  text: string
}

interface Rule {
  kind: TokenKind
  regex: RegExp
  /** Optional post-classifier — used to demote `$step` to a variable but
   *  keep `$sum` as a function based on the symbol table. */
  reclassify?: (text: string) => TokenKind
}

const JSONATA_FUNCTIONS = new Set([
  'sum',
  'count',
  'avg',
  'max',
  'min',
  'string',
  'number',
  'boolean',
  'not',
  'lookup',
  'spread',
  'merge',
  'each',
  'sift',
  'map',
  'reduce',
  'filter',
  'sort',
  'shuffle',
  'distinct',
  'reverse',
  'zip',
  'append',
  'exists',
  'type',
  'length',
  'substring',
  'substringBefore',
  'substringAfter',
  'uppercase',
  'lowercase',
  'trim',
  'pad',
  'contains',
  'split',
  'join',
  'match',
  'replace',
  'now',
  'millis',
  'fromMillis',
  'toMillis',
  'random',
  'floor',
  'ceil',
  'round',
  'abs',
  'power',
  'sqrt',
  'eval',
  'keys',
  'values',
])

const RULES: Rule[] = [
  { kind: 'whitespace', regex: /^\s+/ },
  // Strings: single or double quoted, allow escaped quotes.
  { kind: 'string', regex: /^"(?:\\.|[^"\\])*"/ },
  { kind: 'string', regex: /^'(?:\\.|[^'\\])*'/ },
  // Numbers: integers, decimals, scientific.
  { kind: 'number', regex: /^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/ },
  // `$identifier` — defaults to variable, demotes to function for known
  // JSONata helpers (the only way to tell variables from functions at
  // tokenisation time without a parser).
  {
    kind: 'variable',
    regex: /^\$[A-Za-z_][A-Za-z0-9_]*/,
    reclassify: (text) => (JSONATA_FUNCTIONS.has(text.slice(1)) ? 'function' : 'variable'),
  },
  // `$` alone (e.g. `$.field`) — current context.
  { kind: 'variable', regex: /^\$/ },
  // Property access — colour the dot + identifier together so chained
  // paths read as one continuous accent.
  { kind: 'property', regex: /^\.[A-Za-z_][A-Za-z0-9_]*/ },
  // Bracketed string access (`["foo"]` etc.) — leave punctuation default
  // and let the string rule catch the inner.
  { kind: 'punctuation', regex: /^[()[\]{},;]/ },
  // Binary / unary operators.
  { kind: 'operator', regex: /^(?:=|!=|<=|>=|<|>|&|\?|\||\+|-|\*|\/|%)/ },
  // Bare identifier — last resort.
  { kind: 'identifier', regex: /^[A-Za-z_][A-Za-z0-9_]*/ },
]

export function tokenize(input: string): Token[] {
  const tokens: Token[] = []
  let remaining = input
  while (remaining.length > 0) {
    let matched = false
    for (const rule of RULES) {
      const m = rule.regex.exec(remaining)
      if (!m) continue
      const text = m[0]
      const kind = rule.reclassify ? rule.reclassify(text) : rule.kind
      tokens.push({ kind, text })
      remaining = remaining.slice(text.length)
      matched = true
      break
    }
    if (!matched) {
      // Single character fallback so an unrecognised glyph still appears
      // in the overlay instead of breaking the tokenisation loop.
      tokens.push({ kind: 'unknown', text: remaining[0] })
      remaining = remaining.slice(1)
    }
  }
  return tokens
}

/** Tailwind / CSS classes per token kind. Picked from a dim VS Code-style
 *  palette that works on both light and dark themes. */
export const TOKEN_CLASS: Record<TokenKind, string> = {
  whitespace: '',
  // Strings — soft green, the calmest accent in the palette.
  string: 'text-[#98c379]',
  // Numbers — orange.
  number: 'text-[#d19a66]',
  // `$step`, `$node`, `$item`, etc. — soft blue.
  variable: 'text-[#61afef] font-semibold',
  // JSONata helper functions — warm yellow.
  function: 'text-[#e5c07b] italic',
  // Dotted field access — cyan/teal so chained paths read as one accent.
  property: 'text-[#56b6c2]',
  // Brackets / commas — keep with the body colour.
  punctuation: 'text-[var(--text)]',
  // Operators — purple to call out comparison vs concatenation.
  operator: 'text-[#c678dd]',
  // Bare identifiers (raw names inside a path) — pale foreground.
  identifier: 'text-[var(--text)]',
  // Unknown — same as identifier; never coloured red so a half-typed
  // expression doesn't flash error styling.
  unknown: 'text-[var(--text)]',
}

/**
 * Region helpers for the unified `{{ expression }}` text field.
 *
 * The editor lets users type plain text with embedded `{{ … }}` blocks,
 * e.g. `Re: {{ $step.subject }}`. Completions / highlighting only kick in
 * inside the braces — outside it's free text.
 *
 * Public API:
 * - `findActiveExpressionRegion(text, caret)` — returns the region the
 *   caret is currently inside, or `null` when the caret is in plain text.
 * - `findAllExpressionRegions(text)` — every `{{ … }}` (or unclosed `{{`
 *   trailing the value) in the order they appear; used for highlighting.
 *
 * Regions are tolerant of an unclosed trailing `{{` so the popup opens
 * while the user is mid-type. A `{{` with a `}}` between it and the
 * caret no longer wraps the caret and is therefore not active.
 */

export interface ExpressionRegion {
  /** Index of the leading `{` in `{{`. */
  open: number
  /** Index of the leading `}` in `}}`, or `text.length` if unclosed. */
  close: number
  /** Substring between `{{` and `}}` (excluded), trimmed of surrounding whitespace handled by callers. */
  inner: string
  /** Whether the region has an explicit `}}` close (vs. trailing open). */
  closed: boolean
}

/**
 * Walk backwards from the caret looking for the nearest `{{` that hasn't
 * been closed yet. Returns the region (with caret offset) when the caret
 * sits inside a `{{ … }}` block (or an unclosed trailing `{{`).
 */
export function findActiveExpressionRegion(
  text: string,
  caret: number,
):
  | (ExpressionRegion & {
      /** Caret index inside `inner` (0-based). */
      innerCaret: number
    })
  | null {
  let openIdx = -1
  // Scan backwards from just before the caret. We rely on consecutive
  // ASCII characters so `text.startsWith(needle, i)` (cheaper than substr)
  // is the right primitive here.
  for (let i = caret - 1; i >= 0; i--) {
    if (text[i] === '}' && text[i + 1] === '}') {
      // A `}}` between caret and the next earlier `{{` means we're
      // outside any expression region.
      return null
    }
    if (text[i] === '{' && text[i + 1] === '{') {
      openIdx = i
      break
    }
  }
  if (openIdx === -1) return null

  // The caret is inside `{{ … }}`. Find the corresponding `}}` (treat
  // unclosed-at-end-of-text as "still typing", so the popup keeps
  // showing while the user types the expression body).
  let closeIdx = text.indexOf('}}', caret)
  let closed = true
  if (closeIdx === -1) {
    closeIdx = text.length
    closed = false
  }

  const innerStart = openIdx + 2
  const innerEnd = closeIdx
  return {
    open: openIdx,
    close: closeIdx,
    inner: text.slice(innerStart, innerEnd),
    innerCaret: Math.max(0, Math.min(caret - innerStart, innerEnd - innerStart)),
    closed,
  }
}

/**
 * Enumerate every `{{ … }}` region in the text. Used by the highlight
 * overlay so each region can be coloured independently. Tracks unclosed
 * trailing `{{` so it gets the in-progress style too.
 */
export function findAllExpressionRegions(text: string): ExpressionRegion[] {
  const regions: ExpressionRegion[] = []
  let i = 0
  while (i < text.length) {
    const open = text.indexOf('{{', i)
    if (open === -1) break
    const close = text.indexOf('}}', open + 2)
    if (close === -1) {
      regions.push({
        open,
        close: text.length,
        inner: text.slice(open + 2),
        closed: false,
      })
      break
    }
    regions.push({
      open,
      close,
      inner: text.slice(open + 2, close),
      closed: true,
    })
    i = close + 2
  }
  return regions
}

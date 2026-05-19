import type React from 'react'

export const INTERPOLATION_DRAG_MIME = 'application/x-fuse-interpolation'

const INTERPOLATION_PATTERN = /^\{\{.+\}\}$/

export function buildOutputInterpolation(nodeId: string, path: string[]): string {
  const segments = [nodeId, 'output', ...path.filter(Boolean)]
  return `{{${segments.join('.')}}}`
}

export function writeInterpolationDragData(
  event: React.DragEvent,
  interpolation: string,
): void {
  event.dataTransfer.setData(INTERPOLATION_DRAG_MIME, interpolation)
  event.dataTransfer.setData('text/plain', interpolation)
  event.dataTransfer.effectAllowed = 'copy'
}

export function hasInterpolationDragData(event: React.DragEvent): boolean {
  return Array.from(event.dataTransfer.types).some(
    (type) => type === INTERPOLATION_DRAG_MIME || type === 'text/plain',
  )
}

export function readInterpolationDragData(event: React.DragEvent): string | null {
  const interpolation =
    event.dataTransfer.getData(INTERPOLATION_DRAG_MIME) ||
    event.dataTransfer.getData('text/plain')

  if (!INTERPOLATION_PATTERN.test(interpolation)) return null
  return interpolation
}

export function insertInterpolationAtSelection(
  value: string,
  interpolation: string,
  selectionStart: number,
  selectionEnd: number,
): string {
  const beforeSelection = value.substring(0, selectionStart)
  const normalizedBefore = beforeSelection.endsWith('{{')
    ? beforeSelection.slice(0, -2)
    : beforeSelection

  return normalizedBefore + interpolation + value.substring(selectionEnd)
}

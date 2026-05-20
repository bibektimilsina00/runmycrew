// Mirror of Sim's CONTAINER_DIMENSIONS constants
export const LOOP_DIMS = {
  DEFAULT_WIDTH: 500,
  DEFAULT_HEIGHT: 300,
  HEADER_HEIGHT: 50,
  LEFT_PADDING: 16,
  RIGHT_PADDING: 24,   // tight — just clears the border handle
  TOP_PADDING: 8,
  BOTTOM_PADDING: 24,
}

export const LOOP_START_HANDLE_ID = 'loop-start-source'
export const LOOP_END_HANDLE_ID = 'loop-end-source'

/** Returns smallest containing loop node at the given canvas position, or null. */
export function getContainingLoop(
  position: { x: number; y: number },
  nodes: any[]
): { loopId: string; loopPosition: { x: number; y: number }; dims: { width: number; height: number } } | null {
  const containers = nodes
    .filter(n => n.type === 'logic.loop')
    .filter(n => {
      const lx = n.position.x
      const ly = n.position.y
      const lw = n.data?.width ?? n.width ?? LOOP_DIMS.DEFAULT_WIDTH
      const lh = n.data?.height ?? n.height ?? LOOP_DIMS.DEFAULT_HEIGHT
      return position.x >= lx && position.x <= lx + lw && position.y >= ly && position.y <= ly + lh
    })
    .map(n => ({
      loopId: n.id,
      loopPosition: n.position,
      dims: {
        width: n.data?.width ?? n.width ?? LOOP_DIMS.DEFAULT_WIDTH,
        height: n.data?.height ?? n.height ?? LOOP_DIMS.DEFAULT_HEIGHT,
      },
    }))

  if (containers.length === 0) return null
  // Return smallest (innermost) container
  return containers.sort((a, b) => a.dims.width * a.dims.height - b.dims.width * b.dims.height)[0]
}

/** Clamp a position to be inside the loop body (below header, within padding). */
export function clampToLoopBody(
  relPos: { x: number; y: number },
  containerDims: { width: number; height: number },
  nodeDims: { width: number; height: number } = { width: 200, height: 80 }
): { x: number; y: number } {
  const minX = LOOP_DIMS.LEFT_PADDING
  const minY = LOOP_DIMS.HEADER_HEIGHT + LOOP_DIMS.TOP_PADDING
  const maxX = containerDims.width - LOOP_DIMS.RIGHT_PADDING - nodeDims.width
  const maxY = containerDims.height - LOOP_DIMS.BOTTOM_PADDING - nodeDims.height
  return {
    x: Math.max(minX, Math.min(relPos.x, Math.max(minX, maxX))),
    y: Math.max(minY, Math.min(relPos.y, Math.max(minY, maxY))),
  }
}

/** Calculate loop container dimensions to fit all its children. */
export function calcLoopDims(
  children: Array<{ position: { x: number; y: number }; width?: number; height?: number }>
): { width: number; height: number } {
  if (children.length === 0) {
    return { width: LOOP_DIMS.DEFAULT_WIDTH, height: LOOP_DIMS.DEFAULT_HEIGHT }
  }
  let maxRight = 0
  let maxBottom = 0
  for (const c of children) {
    const w = c.width ?? 200
    const h = c.height ?? 80
    maxRight = Math.max(maxRight, c.position.x + w)
    maxBottom = Math.max(maxBottom, c.position.y + h)
  }
  return {
    width: Math.max(LOOP_DIMS.DEFAULT_WIDTH, LOOP_DIMS.LEFT_PADDING + maxRight + LOOP_DIMS.RIGHT_PADDING),
    height: Math.max(
      LOOP_DIMS.DEFAULT_HEIGHT,
      LOOP_DIMS.HEADER_HEIGHT + LOOP_DIMS.TOP_PADDING + maxBottom + LOOP_DIMS.BOTTOM_PADDING
    ),
  }
}

/** Sort nodes so parent nodes always appear before their children. */
export function sortNodesParentsFirst(nodes: any[]): any[] {
  const map = new Map(nodes.map(n => [n.id, n]))
  const result: any[] = []
  const added = new Set<string>()
  const add = (node: any) => {
    if (added.has(node.id)) return
    if (node.parentNode && !added.has(node.parentNode)) {
      const parent = map.get(node.parentNode)
      if (parent) add(parent)
    }
    result.push(node)
    added.add(node.id)
  }
  nodes.forEach(add)
  return result
}

import { useMemo } from 'react'
import { useShallow } from 'zustand/react/shallow'
import { useCollaborationStore } from '../collaborationStore'

/**
 * Injects a small <style> block that paints a colored outline around
 * every node any peer currently has selected.
 *
 * Why a generated <style> tag rather than React Flow's nodes.className?
 * The same node can be selected by multiple peers; we want each of
 * them to leave a visible ring rather than one peer "winning". Using
 * data-peer-N attributes (set inline by ReactFlow) would require
 * mutating every node on every selection event — generating CSS once
 * per peer-selection diff is cheaper and contained.
 *
 * React Flow already adds a `data-id="<node-id>"` attribute to every
 * `.react-flow__node`, so the selector is just an attribute match.
 */
export function PeerSelectionStyles() {
  const peers = useCollaborationStore(useShallow((s) => Object.values(s.peers)))

  const css = useMemo(() => {
    if (peers.length === 0) return ''
    const rules: string[] = []
    for (const peer of peers) {
      if (peer.selectedNodeIds.length === 0) continue
      const selectors = peer.selectedNodeIds
        .map((id) => `.react-flow__node[data-id="${cssEscape(id)}"]`)
        .join(',')
      // 0 0 0 2px = solid ring; outer 6px = soft glow. Using outline
      // (not border) so the node geometry isn't shifted when a peer
      // selection appears.
      rules.push(
        `${selectors}{outline:2px solid ${peer.session.color} !important;outline-offset:2px;border-radius:inherit;box-shadow:0 0 0 6px ${peer.session.color}22}`,
      )
    }
    return rules.join('\n')
  }, [peers])

  if (!css) return null
  return <style>{css}</style>
}

/** Subset of CSS.escape sufficient for UUID-style node ids. */
function cssEscape(value: string): string {
  return value.replace(/["\\]/g, '\\$&')
}

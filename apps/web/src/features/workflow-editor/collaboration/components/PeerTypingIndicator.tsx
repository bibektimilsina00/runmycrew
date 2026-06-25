import { useCollaborationStore } from '../collaborationStore'

/**
 * Inline "X is editing this node" badge. Mount inside the inspector
 * for the currently-selected node; renders nothing when no peer is
 * typing in that node.
 */
export function PeerTypingIndicator({ nodeId }: { nodeId: string | null | undefined }) {
  const peer = useCollaborationStore((s) => {
    if (!nodeId) return null
    for (const p of Object.values(s.peers)) {
      if (p.typingNodeId === nodeId) return p
    }
    return null
  })

  if (!peer) return null

  return (
    <div
      className="inline-flex items-center gap-1.5 rounded-[5px] px-2 py-[3px] text-[10.5px] font-medium text-white"
      style={{ backgroundColor: peer.session.color }}
    >
      <span className="relative inline-flex h-[6px] w-[6px]">
        <span
          className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
          style={{ backgroundColor: 'white' }}
        />
        <span
          className="relative inline-flex h-[6px] w-[6px] rounded-full"
          style={{ backgroundColor: 'white' }}
        />
      </span>
      {peer.session.user_name} is editing
    </div>
  )
}

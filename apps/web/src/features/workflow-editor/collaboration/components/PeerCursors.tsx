import { useReactFlow } from 'reactflow'
import { useShallow } from 'zustand/react/shallow'
import { useCollaborationStore } from '../collaborationStore'

/**
 * Renders peer cursors as colored arrows + name labels at the peers'
 * stored canvas-space positions. Mounts inside ReactFlow so the cursor
 * tracks pan + zoom — coordinates broadcast over the wire are always
 * in canvas (flow) coordinates, and we let `useReactFlow().flowToScreen`
 * convert them to screen pixels on each render.
 */
export function PeerCursors() {
  const peers = useCollaborationStore(useShallow((s) => Object.values(s.peers)))
  const { flowToScreenPosition } = useReactFlow()

  if (peers.length === 0) return null

  return (
    <div className="pointer-events-none absolute inset-0 z-50">
      {peers.map(({ session, cursor }) => {
        if (!cursor) return null
        const screen = flowToScreenPosition(cursor)
        return (
          <div
            key={session.session_id}
            className="absolute transition-transform duration-75 ease-linear"
            style={{
              transform: `translate(${screen.x}px, ${screen.y}px)`,
            }}
          >
            <svg width="14" height="18" viewBox="0 0 14 18" fill="none">
              <path
                d="M1 1L13 7.5L7 9.5L4.5 15.5L1 1Z"
                fill={session.color}
                stroke="white"
                strokeWidth="1"
                strokeLinejoin="round"
              />
            </svg>
            <span
              className="absolute left-[14px] top-[14px] rounded-[4px] px-1.5 py-[2px] text-[10px] font-medium text-white whitespace-nowrap shadow-sm"
              style={{ backgroundColor: session.color }}
            >
              {session.user_name}
            </span>
          </div>
        )
      })}
    </div>
  )
}
